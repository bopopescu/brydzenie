# Copyright 2015 Google Inc. All Rights Reserved.

"""A class for projecting and transforming JSON-serializable objects.

Example usage:

  projector = resource_projector.Compile(expression)
  for resource in resources:
    obj = projector.Evaluate(resource)
    OperateOnProjectedResource(obj)
"""

from protorpc import messages

from apitools.base.py import encoding
from googlecloudsdk.core.resource import resource_projection_parser
from googlecloudsdk.core.resource import resource_property


def MakeSerializable(resource):
  """Returns resource or a JSON-serializable copy of resource.

  Args:
    resource: The resource object.

  Returns:
    The original resource if it is a primitive type object, otherwise a
    JSON-serializable copy of resource.
  """
  return Compile().Evaluate(resource)


def ClassToDict(resource):
  """Converts a resource class object to a dict.

  Private and callable attributes are omitted in the dict.

  Args:
    resource: The class object to convert.

  Returns:
    The dict representing the class object.
  """
  r = {}
  for attr in dir(resource):
    if attr.startswith('_'):
      # Omit private attributes.
      continue
    value = getattr(resource, attr)
    if hasattr(value, '__call__'):
      # Omit callable attributes.
      continue
    r[attr] = value
  return r


class Projector(object):
  """Projects a resource using a ProjectionSpec.

  A projector is a method that takes an object and a projection as input and
  produces a new JSON-serializable object containing only the values
  corresponding to the keys in the projection. Optional projection key
  attributes may transform the values in the resulting JSON-serializable object.

  Attributes:
    _by_columns: True if Projector projects to a list of columns.
  """

  def __init__(self, projection, by_columns=False):
    """Constructor.

    Args:
      projection: A ProjectionSpec (parsed resource projection expression).
      by_columns: Project to a list of columns if True.
    """
    self._projection = projection
    self._by_columns = by_columns

  def _ProjectAttribute(self, obj, projection, flag):
    """Applies projection.attribute.transform in projection if any to obj.

    Args:
      obj: An object.
      projection: Projection _Tree node.
      flag: A bitmask of DEFAULT, INNER, PROJECT.

    Returns:
      The transformed obj if there was a transform, otherwise the original obj.
    """
    if flag < self._projection.PROJECT:
      # Unprojected values are skipped.
      return None
    if projection and projection.attribute and projection.attribute.transform:
      # Transformed values end the DFS on this branch of the tree.
      transform = projection.attribute.transform
      return transform.func(obj, *transform.args, **transform.kwargs)
    # leaf=True makes sure we don't get back here with the same obj.
    return self._Project(obj, projection, flag, leaf=True)

  def _ProjectDict(self, obj, projection, flag):
    """Projects a dictionary object.

    Args:
      obj: A dict.
      projection: Projection _Tree node.
      flag: A bitmask of DEFAULT, INNER, PROJECT.

    Returns:
      The projected obj.
    """
    if not obj:
      return obj
    res = {}
    for key, val in obj.iteritems():
      if key in projection.tree:
        child_projection = projection.tree[key]
        f = flag | child_projection.attribute.flag
        if f < self._projection.INNER:
          # This branch of the tree is dead.
          continue
        # This branch of the tree is still alive. self._Project() returns
        # None if there are no actual PROJECT hits below.
        val = self._Project(val, child_projection, f)
      else:
        val = self._ProjectAttribute(val, self._projection.GetEmpty(), flag)
      if val is not None:
        # Only record successful projections.
        res[str(key)] = val
    return res or None

  def _ProjectList(self, obj, projection, flag):
    """Projects a list or tuple object.

    Args:
      obj: A list or tuple.
      projection: Projection _Tree node.
      flag: A bitmask of DEFAULT, INNER, PROJECT.

    Returns:
      The projected obj.
    """
    if not obj:
      return obj
    # Determine the explicit indices or slice.
    # If there is a slice index then every index is projected.
    indices = set([])
    sliced = None
    if not projection.tree:
      # With no projection tree its all or nothing.
      if flag < self._projection.PROJECT:
        return None
    else:
      # Glean indices from the projection tree.
      for index in projection.tree:
        if index is None:
          if (flag >= self._projection.PROJECT or
              projection.tree[index].attribute.flag):
            sliced = projection.tree[index]
        elif (isinstance(index, (int, long)) and
              index in xrange(-len(obj), len(obj))):
          indices.add(index)

    # Everything below a PROJECT node is projected.
    if flag >= self._projection.PROJECT and not sliced:
      sliced = self._projection.GetEmpty()

    # If there are no indices to match then nothing is projected.
    if not indices and not sliced:
      return None

    # Keep track of the max index projected.
    maxindex = -1
    if sliced:
      # A slice covers all indices.
      res = [None] * (len(obj))
    else:
      # Otherwise the result only includes the largest explict index.
      res = [None] * (max(x + len(obj) if x < 0 else x for x in indices) + 1)
    for index in range(len(obj)) if sliced else indices:
      val = obj[index]

      # Can't project something from nothing.
      if val is None:
        continue

      # Determine the child node projection.
      f = flag
      if index in projection.tree:
        # Explicit index in projection overrides slice.
        child_projection = projection.tree[index]
        if sliced:
          # Except the slice flag still counts.
          f |= sliced.attribute.flag
      else:
        # slice provides defaults for indices that are not explicit.
        child_projection = sliced

      # Now determine the value.
      if child_projection:
        f |= child_projection.attribute.flag
        if f >= self._projection.INNER:
          # This branch of the tree is still alive. self._Project() returns
          # None if there are no actual PROJECT hits below.
          val = self._Project(val, child_projection, f)
        else:
          val = None

      # Don't record empty projections.
      if val is None:
        continue
      # Record the highest index so the rest can be stripped.
      if index < 0:
        index += len(obj)
      if maxindex < index:
        maxindex = index
      res[index] = val

    # If nothing was projected return None instead of a list of all None items.
    if maxindex < 0:
      return None

    # Some non-None elements. slice strips trailing None elements.
    return res[0:maxindex + 1] if sliced else res

  def _Project(self, obj, projection, flag, leaf=False):
    """Evaluate() helper function.

    tl;dr This function takes a resource obj and a preprocessed projection. obj
    is a dense subtree of the resource schema (some keys values may be missing)
    and projection is a sparse, possibly improper, subtree of the resource
    schema. Improper in that it may contain paths that do not exist in the
    resource schema or object. _Project() traverses both trees simultaneously,
    guided by the projection tree. When a projection tree path reaches an
    non-existent obj tree path the projection tree traversal is pruned. When a
    projection tree path terminates with an existing obj tree path, that obj
    tree value is projected and the obj tree traversal is pruned.

    Since resources can be sparse a projection can reference values not present
    in a particular resource. Because of this the code is lenient on out of
    bound conditions that would normally be errors.

    Args:
      obj: An object.
      projection: Projection _Tree node.
      flag: A bitmask of DEFAULT, INNER, PROJECT.
      leaf: Do not call _ProjectAttribute() if True.

    Returns:
      An object containing only the key:values selected by projection, or obj if
      the projection is None or empty.
    """
    if obj is None:
      pass
    elif isinstance(obj, (basestring, bool, int, long, float, complex)):
      # primitive data type
      pass
    elif isinstance(obj, bytearray):
      # bytearray copied to disassociate from original obj.
      obj = str(obj)
    else:
      if isinstance(obj, messages.Message):
        # protorpc message.
        obj = encoding.MessageToDict(obj)
      elif not hasattr(obj, '__iter__') or hasattr(obj, '_fields'):
        # class object or collections.namedtuple() (via the _fields test).
        obj = ClassToDict(obj)
      if hasattr(obj, 'next'):
        # Generator object.
        try:
          obj = obj.next()
        except StopIteration:
          obj = None
        return self._Project(obj, projection, flag, leaf)
      if projection and projection.attribute and projection.attribute.transform:
        # Transformed nodes prune here.
        transform = projection.attribute.transform
        return transform.func(obj, *transform.args, **transform.kwargs)
      if ((flag >= self._projection.PROJECT or projection and projection.tree)
          and hasattr(obj, '__iter__')):
        if hasattr(obj, 'iteritems'):
          return self._ProjectDict(obj, projection, flag)
        else:
          return self._ProjectList(obj, projection, flag)
    return obj if leaf else self._ProjectAttribute(obj, projection, flag)

  def SetByColumns(self, enable):
    """Sets the projection to list-of-columns state.

    Args:
      enable: Enables projection to a list-of-columns if True.
    """
    self._by_columns = enable

  def Evaluate(self, obj):
    """Serializes/projects/transforms one or more objects.

    A default or empty projection expression simply converts a resource object
    to a JSON-serializable copy of the object.

    Args:
      obj: An object.

    Returns:
      A JSON-serializeable object containing only the key values selected by
        the projection. The return value is a deep copy of the object: changes
        to the input object do not affect the JSON-serializable copy.
    """
    if not self._by_columns or not self._projection.Columns():
      flag = (self._projection.DEFAULT if self._projection.Columns()
              else self._projection.PROJECT)
      return self._Project(obj, self._projection.Tree(), flag)
    columns = []
    for column in self._projection.Columns():
      val = resource_property.Get(obj, column.key) if column.key else obj
      transform = column.attribute.transform
      if transform:
        val = transform.func(val, *transform.args, **transform.kwargs)
      columns.append(val)
    return columns

  def Projection(self):
    """Returns the ProjectionSpec object for the projector.

    Returns:
      The ProjectionSpec object for the projector.
    """
    return self._projection


def Compile(expression='', defaults=None, symbols=None, by_columns=False):
  """Compiles a resource projection expression.

  Args:
    expression: The resource projection string.
    defaults: resource_projection_spec.ProjectionSpec defaults.
    symbols: Transform function symbol table dict indexed by function name.
    by_columns: Project to a list of columns if True.

  Returns:
    A Projector containing the compiled expression ready for Evaluate().
  """
  projection = resource_projection_parser.Parse(expression, defaults=defaults,
                                                symbols=symbols)
  return Projector(projection, by_columns=by_columns)
