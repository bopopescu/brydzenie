# Copyright 2015 Google Inc. All Rights Reserved.

"""call sets list command."""

from apitools.base import py as apitools_base
from googlecloudsdk.calliope import base
from googlecloudsdk.core.util import list_printer
from googlecloudsdk.genomics import lib
from googlecloudsdk.genomics.lib import genomics_util


class List(base.Command):
  """List genomics call sets in a project.

  Prints a table with summary information on call sets in the project.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'variant_set_ids',
        nargs='+',
        help="""Restrict the query to call sets within the given variant sets.
             At least one ID must be provided.""")

    parser.add_argument(
        '--name',
        help="""Only return call sets for which a substring of the
             name matches this string.""")

    parser.add_argument(
        '--limit',
        type=int,
        help='The maximum number of results to list.')

  @genomics_util.ReraiseHttpException
  def Run(self, args):
    """Run 'callsets list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of callsets matching the given variant set ids.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    genomics_util.ValidateLimitFlag(args.limit)

    apitools_client = self.context[lib.GENOMICS_APITOOLS_CLIENT_KEY]
    req_class = (self.context[lib.GENOMICS_MESSAGES_MODULE_KEY]
                 .SearchCallSetsRequest)
    request = req_class(
        name=args.name,
        variantSetIds=args.variant_set_ids)
    res = apitools_base.list_pager.YieldFromList(
        apitools_client.callsets,
        request,
        method='Search',
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=None,  # Use server default.
        field='callSets')

    return res

  def Display(self, args, result):
    """Display prints information about what just happened to stdout.

    Args:
      args: The same as the args in Run.

      result: a list of CallSet objects.

    Raises:
      ValueError: if result is None or not a list
    """
    list_printer.PrintResourceList('genomics.callSets', result)
