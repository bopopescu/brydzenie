# Copyright 2014 Google Inc. All Rights Reserved.

"""instance-groups add-service command."""

from apiclient import errors
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.preview.lib import util


class ListServices(base.Command):
  """List the services for an instance group or instance resource.

  *{command}* lists the services (name and port tuples) for all
  instances in an instance group.

  Please see the API documentation for more details.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('name', help='Instance group name.')

  def Run(self, args):
    """Run 'instance-groups list-services'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      the API response.

    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing
          the command.
    """
    log.warn('Please use instead [gcloud compute instance-groups '
             'unmanaged get-named-ports].')
    client = self.context['instanceGroupsClient']
    project = properties.VALUES.core.project.Get(required=True)
    get_request = client.getService(
        project=project,
        zone=args.zone,
        resourceView=args.name)

    try:
      response = get_request.execute()
      util.PrettyPrint(response)
      return response
    except errors.HttpError as error:
      raise exceptions.HttpException(util.GetError(error))
    except errors.Error as error:
      raise exceptions.ToolException(error)
