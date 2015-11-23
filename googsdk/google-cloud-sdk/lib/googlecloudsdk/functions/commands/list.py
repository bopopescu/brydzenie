# Copyright 2015 Google Inc. All Rights Reserved.

"""'functions list' command."""

import sys

from googlecloudsdk.core import properties

from apitools.base import py as apitools_base
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core.util import list_printer


class List(base.Command):
  """Lists all the functions in a given region."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--limit', default=None,
        help='If greater than zero, the maximum number of results.',
        type=arg_parsers.BoundedInt(1, sys.maxint))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A list object representing user functions.
    """
    client = self.context['functions_client']
    return apitools_base.YieldFromList(
        service=client.projects_regions_functions,
        request=self.BuildRequest(args),
        limit=args.limit, field='functions',
        batch_size_attribute='pageSize')

  def BuildRequest(self, args):
    """This method creates a ListRequest message to be send to GCF.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A ListRequest message.
    """
    messages = self.context['functions_messages']
    project = properties.VALUES.core.project.Get(required=True)
    location = 'projects/{0}/regions/{1}'.format(
        project, args.region)
    return messages.CloudfunctionsProjectsRegionsFunctionsListRequest(
        location=location)

  def Display(self, unused_args, result):
    """This method is called to print the result of the Run() method.

    Args:
      unused_args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    list_printer.PrintResourceList('functions.projects.regions.functions',
                                   result)
