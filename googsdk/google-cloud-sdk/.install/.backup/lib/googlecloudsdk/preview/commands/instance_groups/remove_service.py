# Copyright 2014 Google Inc. All Rights Reserved.

"""instance-groups remove-service command."""

from apiclient import errors
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.preview.lib import resource_view_service_util as service_util
from googlecloudsdk.preview.lib import util


class RemoveService(base.Command):
  """Remove a service from an instance group or an instance in it.

  *{command}* removes a service (name and port) from one or all instances
  in an instance group.

  The service is removed from the instance group itself,
  which makes it take effect on all instances in the instance group.

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
    parser.add_argument(
        '--service', required=True, help='Name of the service.')

  def Run(self, args):
    """Run 'instance-groups remove-service'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing
          the command.
    """
    log.warn('Please use instead [gcloud compute instance-groups '
             'unmanaged set-named-ports].')
    client = self.context['instanceGroupsClient']
    project = properties.VALUES.core.project.Get(required=True)

    get_request = client.getService(
        project=project,
        zone=args.zone,
        resourceView=args.name)

    try:
      get_response = get_request.execute()
    except errors.HttpError as error:
      raise exceptions.HttpException(util.GetError(error))
    except errors.Error as error:
      raise exceptions.ToolException(error)

    request_body = {}
    request_body['fingerprint'] = get_response['fingerprint']
    endpoints = None
    if 'endpoints' in get_response:
      endpoints = get_response['endpoints']

    request_body['endpoints'] = service_util.RemoveServiceFromEndpoints(
        args.service, endpoints)

    set_request = client.setService(
        project=project,
        zone=args.zone,
        resourceView=args.name,
        body=request_body)

    try:
      set_request.execute()
      log.Print('Service {0} removed.'.format(args.service))
    except errors.HttpError as error:
      raise exceptions.HttpException(util.GetError(error))
    except errors.Error as error:
      raise exceptions.ToolException(error)
