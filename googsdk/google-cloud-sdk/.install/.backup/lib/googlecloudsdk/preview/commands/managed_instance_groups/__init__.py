# Copyright 2014 Google Inc. All Rights Reserved.

"""The command-group for the Managed Instance Group service CLI."""

from googlecloudsdk.core import log
from googlecloudsdk.core import properties

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources
from googlecloudsdk.core.credentials import store


class InstanceGroupManagers(base.Group):
  """Managed Instance Groups client."""

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
        '--zone', required=True, help='Managed instance group\'s zone name.',
        action=actions.StoreProperty(properties.VALUES.compute.zone))

  @exceptions.RaiseToolExceptionInsteadOf(store.Error)
  def Filter(self, context, args):
    """Context() is a filter function that can update the context.

    Args:
      context: The current context.
      args: The argparse namespace that was specified on the CLI or API.

    Returns:
      The updated context.
    """
    log.warn('This preview command group will be removed soon.')
    log.warn('These managed infrastructure preview commands have been migrated '
             'to "gcloud compute instance-groups managed" command group.')
    log.warn('See https://cloud.google.com/sdk/gcloud/reference/ for more '
             'details.')

    # pylint:disable=g-import-not-at-top, Delaying import for performance.
    import apiclient.discovery as discovery

    # Create the Managed Instance Group service client
    api_server = properties.VALUES.core.api_host.Get()
    api_version = args.api_version

    discovery_url = ('{server}/discovery/v1/apis/replicapool/{version}/rest'
                     .format(server=api_server.rstrip('/'),
                             version=api_version))
    http = self.Http()
    client = discovery.build(
        'replicapool', api_version, http=http,
        discoveryServiceUrl=discovery_url)
    context['managedInstanceGroupsClient'] = client

    return context
