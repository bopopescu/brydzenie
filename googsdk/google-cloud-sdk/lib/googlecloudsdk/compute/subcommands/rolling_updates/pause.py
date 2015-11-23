# Copyright 2014 Google Inc. All Rights Reserved.

"""rolling-updates pause command."""

from googlecloudsdk.core import log

from apitools.base import py as apitools_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.compute.lib import rolling_updates_util as updater_util


class Pause(base.Command):
  """Pauses an existing update."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('update', help='Update id.')
    # TODO(user): Support --async which does not wait for state transition.

  def Run(self, args):
    """Run 'rolling-updates pause'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Raises:
      HttpException: An http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing
          the command.
    """
    client = self.context['updater_api']
    messages = self.context['updater_messages']
    resources = self.context['updater_resources']

    ref = resources.Parse(
        args.update,
        collection='replicapoolupdater.rollingUpdates')
    request = messages.ReplicapoolupdaterRollingUpdatesPauseRequest(
        project=ref.project,
        zone=ref.zone,
        rollingUpdate=ref.rollingUpdate)

    try:
      operation = client.rollingUpdates.Pause(request)
      operation_ref = resources.Parse(
          operation.name,
          collection='replicapoolupdater.zoneOperations')
      result = updater_util.WaitForOperation(
          client, operation_ref, 'Pausing the update')
      if result:
        log.status.write('Paused [{0}].\n'.format(ref))
      else:
        raise exceptions.ToolException('could not pause [{0}]'.format(ref))

    except apitools_base.HttpError as error:
      raise exceptions.HttpException(updater_util.GetError(error))

Pause.detailed_help = {
    'brief': 'Pauses an existing update.',
    'DESCRIPTION': """\
        Pauses the update in state ROLLING_FORWARD, ROLLING_BACK or PAUSED \
        (fails if the update is in any other state).
        No-op if invoked in state PAUSED.
        """,
}
