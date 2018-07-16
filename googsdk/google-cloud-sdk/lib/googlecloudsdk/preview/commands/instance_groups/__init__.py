# Copyright 2014 Google Inc. All Rights Reserved.

"""The super-group for the Instance Groups CLI."""

from googlecloudsdk.core import log
from googlecloudsdk.core import properties

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.credentials import store


class InstanceGroups(base.Group):
  """Manage Cloud Instance Groups."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        '--api-version', default='v1beta2', help='Optional API version.')
    parser.add_argument(
        '--zone', required=True, help='Instance group zone name.',
        action=actions.StoreProperty(properties.VALUES.compute.zone))

  @exceptions.RaiseToolExceptionInsteadOf(store.Error)
  def Filter(self, context, args):
    """Context() is a filter function that can update the context.

    Args:
      context: The current context.
      args: The argparse namespace that was specified on the CLI or API.
    Raises:
      ToolException: if the zone or region flags are provided together or
        are not provided at all.
    Returns:
      The updated context.
    """
    log.warn('This preview command will be removed soon.')
    log.warn('These managed infrastructure preview commands have been migrated '
             'to "gcloud compute instance-groups unmanaged" command group.')
    log.warn('See https://cloud.google.com/sdk/gcloud/reference/ for more '
             'details.')

    # pylint:disable=g-import-not-at-top, Delaying import for performance.
    import apiclient.discovery as discovery

    api_server = properties.VALUES.core.api_host.Get()
    api_version = args.api_version

    discovery_url = ('{server}/discovery/v1/apis/resourceviews/{version}/rest'
                     .format(server=api_server.rstrip('/'),
                             version=api_version))
    http = self.Http()
    client = discovery.build(
        'resourceviews', api_version, http=http,
        discoveryServiceUrl=discovery_url)

    context['instanceGroupsClient'] = client.zoneViews()
    return context
