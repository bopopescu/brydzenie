# Copyright 2015 Google Inc. All Rights Reserved.

"""Cloud resource list filter expression parser.

Left-factorized BNF Grammar:

  expr        : adjterm exprtail            # gcloud: LF has andterm here

  exprtail    : nil
              | adjterm

  adjterm     : orterm adjtail

  adjtail     : nil
              | or orterm

  orterm      : andterm ortail

  ortail      : nil
              | and andterm

  andterm     : term
              | not term

  term        : key operator operand
              | '-'key operator operand
              | function '(' args ')'
              | '(' expr ')'

  key         : member keytail

  keytail     : nil
              | '.' key
              | '.' function '(' args ')'   # gcloud: LF extension

  member      : name
              | name [ integer ]            # gcloud: LF extension
              | name [ ]                    # gcloud: LF extension

  args        : nil
              | arglist

  arglist     | operand arglisttail

  arglisttail : nil
              | ',' arglist

  and       := 'AND'
  not       := 'NOT'
  or        := 'OR'
  operator  := ':' | '=' | '<' | '<=' | '>=' | '>' | '!='
  function  := < name in symbol table >
  name      := < resource identifier name >
  operand   := < token terminated by <space> | '(' | ')' | <EndOfInput> >
  integer   := < positive or negative integer >

Example:
  expression = filter-expression-string
  resources = [JSON-serilaizable-object]

  query = resource_filter.Compile(expression)
  for resource in resources:
    if query.Evaluate(resource):
      ProcessMatchedResource(resource)
"""

from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_expr
from googlecloudsdk.core.resource import resource_lex


class _Parser(object):
  """List filter expression parser.

  Attributes:
    _CONNECTIVE: List of connective and negate operator names.
    _OPERATOR: Search term operator class map indexed by operator name.
    _backend: The expression tree generator module.
    _lex: The resource_lex.Lexer filter expression lexer.
    _operator_char_1: The first char of all search term operators.
    _operator_char_2: The second char of all search term operators.
    _parenthesize: A list of _OP_* bitmasks for each (...) level. Used to
      enforce parenthesization when AND, OR and ADJ are combined in the same
      parenthesis group. One-platform insists on non-standard AND/OR precedence,
      we insist on parenthesization to remove all doubt on the user's intent.
    _symbols: Filter function symbol table dict indexed by function name.
  """
  _OP_AND = 1
  _OP_OR = 2

  _CONNECTIVE = ['AND', 'NOT', 'OR']

  def __init__(self, symbols=None, backend=resource_expr):
    """Constructor.

    Args:
      symbols: Filter function symbol table dict indexed by function name.
      backend: The backend expression tree generator module.
    """

    self._symbols = {}
    if symbols:
      self._symbols.update(symbols)
    self._backend = backend or resource_expr
    self._operator_char_1 = ''
    self._operator_char_2 = ''
    self._operator = {
        ':': self._backend.ExprHAS, '=': self._backend.ExprEQ,
        '!=': self._backend.ExprNE, '<': self._backend.ExprLT,
        '<=': self._backend.ExprLE, '>=': self._backend.ExprGE,
        '>': self._backend.ExprGT}
    # Operator names are length 1 or 2. This loop precomputes _operator_char_1
    # and _operator_char_2 for _ParseOperator to determine both valid and
    # invalid operator names.
    for operator in self._operator:
      c = operator[0]
      if c not in self._operator_char_1:
        self._operator_char_1 += c
      if len(operator) < 2:
        continue
      c = operator[1]
      if c not in self._operator_char_2:
        self._operator_char_2 += c
    self._lex = None
    self._parenthesize = [0]

  def _CheckParenthesization(self, op):
    if self._parenthesize[-1] & ~op:
      raise resource_exceptions.ExpressionSyntaxError(
          'Parenthesis grouping is required when AND and OR are '
          'are combined [{0}].'.format(self._lex.Annotate()))
    self._parenthesize[-1] |= op

  def _ParseOperator(self):
    """Parses an operator token.

    All operators match the RE [_operator_char_1][_operator_char_2], invalid
    operators are 2 character sequences that are not valid operators and
    match the RE [_operator_char_1][_operator_char_1+_operator_char_2].

    Raises:
      ExpressionSyntaxError: The operator spelling is malformed.

    Returns:
      The operator backend expression, None if the next token is not an
      operator.
    """
    if not self._lex.SkipSpace():
      return None
    here = self._lex.GetPosition()
    op = self._lex.IsCharacter(self._operator_char_1)
    if not op:
      return None
    if not self._lex.EndOfInput():
      o2 = self._lex.IsCharacter(self._operator_char_1 + self._operator_char_2)
      if o2:
        op += o2
    if op not in self._operator:
      raise resource_exceptions.ExpressionSyntaxError(
          'Malformed operator [{0}].'.format(self._lex.Annotate(here)))
    self._lex.SkipSpace(token='Term operand')
    return self._operator[op]

  def _ParseTerm(self, must=False):
    """Parses a [-]<key> <operator> <operand> term.

    Args:
      must: Raises ExpressionSyntaxError if must is True and there is no
        expression.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      The new backend expression tree.
    """
    here = self._lex.GetPosition()
    if not self._lex.SkipSpace():
      if must:
        raise resource_exceptions.ExpressionSyntaxError(
            'Term expected [{0}].'.format(self._lex.Annotate(here)))
      return None

    # Check for (...) term.
    if self._lex.IsCharacter('('):
      self._parenthesize.append(0)
      tree = self._ParseExpr()
      self._lex.IsCharacter(')')
      self._parenthesize.pop()
      return tree

    # Check for end of (...) term.
    if self._lex.IsCharacter(')', peek=True):
      return None

    # Parse the key.
    invert = self._lex.IsCharacter('-')
    here = self._lex.GetPosition()
    key = self._lex.Key()
    if key and key[0] in self._CONNECTIVE:
      raise resource_exceptions.ExpressionSyntaxError(
          'Term expected [{0}].'.format(self._lex.Annotate(here)))
    if self._lex.IsCharacter('(', eoi_ok=True):
      # global restriction function or key transform
      args = self._lex.Args(convert=True)
      name = key.pop()
      if name not in self._symbols:
        # Symbol table lookup could be delayed until evaluation time, but
        # catching errors early on is good practice in the Cloud SDK. Otherwise:
        # - a filter expression applied client-side could fetch part or all of
        #   a server resource before failing
        # - a filter expression applied server-side (not implemented yet) would
        #   add another client-server failure case to handle
        # Doing the symbol table lookup here makes the return value of Compile()
        # a hermetic unit. This will make it easier (in the future) to:
        # - apply optimizations based on function semantics
        # - apply client-side vs server-side expression splitting
        raise resource_exceptions.ExpressionSyntaxError(
            'Unknown filter function [{0}].'.format(self._lex.Annotate(here)))
      transform = self._symbols[name]
    else:
      transform = None
      args = None

    # Parse the operator.
    here = self._lex.GetPosition()
    operator = self._ParseOperator()
    if not operator:
      if transform and not key:
        # global restriction function
        tree = self._backend.ExprGlobal(transform, args)
      elif len(key) == 1:
        # global restriction on key[0]
        tree = self._backend.ExprGlobal(self._symbols['global'], key)
      else:
        raise resource_exceptions.ExpressionSyntaxError(
            'Operator expected [{0}].'.format(self._lex.Annotate(here)))
      if invert:
        tree = self._backend.ExprNOT(tree)
      return tree

    # Parse the operand.
    self._lex.SkipSpace(token='Operand')
    here = self._lex.GetPosition()
    operand = self._lex.Token('()')
    if operand is None or operand.split()[0] in self._CONNECTIVE:
      raise resource_exceptions.ExpressionSyntaxError(
          'Term operand expected [{0}].'.format(self._lex.Annotate(here)))

    # Make Expr node for the term.
    tree = operator(key=key, operand=self._backend.ExprOperand(operand),
                    transform=transform, args=args)
    if invert:
      tree = self._backend.ExprNOT(tree)
    return tree

  def _ParseAndTerm(self, must=False):
    """Parses an andterm term.

    Args:
      must: Raises ExpressionSyntaxError if must is True and there is no
      expression.

    Returns:
      The new backend expression tree.
    """
    if self._lex.IsString('NOT'):
      return self._backend.ExprNOT(self._ParseTerm(must=True))
    return self._ParseTerm(must=must)

  def _ParseOrTail(self, tree):
    """Parses an ortail term.

    Args:
      tree: The backend expression tree.

    Returns:
      The new backend expression tree.
    """
    if self._lex.IsString('AND'):
      self._CheckParenthesization(self._OP_AND)
      tree = self._backend.ExprAND(tree, self._ParseAndTerm(must=True))
    return tree

  def _ParseOrTerm(self, must=False):
    """Parses an orterm term.

    Args:
      must: Raises ExpressionSyntaxError if must is True and there is no
        expression.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      The new backend expression tree.
    """
    tree = self._ParseAndTerm()
    if tree:
      tree = self._ParseOrTail(tree)
    elif must:
      raise resource_exceptions.ExpressionSyntaxError(
          'Term expected [{0}].'.format(self._lex.Annotate()))
    return tree

  def _ParseAdjTail(self, tree):
    """Parses a adjtail term.

    Args:
      tree: The backend expression tree.

    Returns:
      The new backend expression tree.
    """
    if self._lex.IsString('OR'):
      self._CheckParenthesization(self._OP_OR)
      tree = self._backend.ExprOR(tree, self._ParseOrTerm(must=True))
    return tree

  def _ParseAdjTerm(self, must=False):
    """Parses a adjterm term.

    Args:
      must: bool, ExpressionSyntaxError if must is True and there is no
        expression.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      The new backend expression tree.
    """
    tree = self._ParseOrTerm()
    if tree:
      tree = self._ParseAdjTail(tree)
    elif must:
      raise resource_exceptions.ExpressionSyntaxError(
          'Term expected [{0}].'.format(self._lex.Annotate()))
    return tree

  def _ParseExprTail(self, tree):
    """Parses an exprtail term.

    Args:
      tree: The backend expression tree.

    Returns:
      The new backend expression tree.
    """
    if (not self._lex.IsString('AND', peek=True) and
        not self._lex.IsString('OR', peek=True) and
        not self._lex.IsCharacter(')', peek=True) and
        not self._lex.EndOfInput()):
      tree = self._backend.ExprAND(tree, self._ParseAdjTerm(must=True))
    return tree

  def _ParseExpr(self):
    """Parses an expr term.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      The new backend expression tree.
    """
    tree = self._ParseAdjTerm()
    if tree:
      tree = self._ParseExprTail(tree)
    return tree

  def Parse(self, expression, aliases=None):
    """Parses the resource list filter expression.

    This is a hand-rolled recursive descent parser based directly on the
    left-factorized BNF grammar in the file docstring.

    Args:
      expression: A resource list filter expression string.
      aliases: Resource key alias dictionary.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      tree: The backend expression tree.
    """
    self._lex = resource_lex.Lexer(expression, aliases=aliases)
    tree = self._ParseExpr()
    if not self._lex.EndOfInput():
      raise resource_exceptions.ExpressionSyntaxError(
          'Unexpected tokens [{0}] in expression.'.format(self._lex.Annotate()))
    self._lex = None
    return tree or self._backend.ExprTRUE()


def Compile(expression, symbols=None, aliases=None, backend=None):
  """Compiles a resource list filter expression.

  Example:
    query = resource_filter.Compile(expression)
    for resource in resources:
      if query.Evaluate(resource):
        ProcessMatchedResource(resource)

  Args:
    expression: A resource list filter expression string.
    symbols: Filter function symbol table dict indexed by function name.
    aliases: Resource key alias dictionary.
    backend: The backend expression tree generator module, resource_expr
      if None.

  Returns:
    A backend expression tree.
  """
  return _Parser(symbols=symbols, backend=backend).Parse(expression,
                                                         aliases=aliases)
