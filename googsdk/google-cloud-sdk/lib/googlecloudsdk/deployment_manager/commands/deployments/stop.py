# Copyright 2014 Google Inc. All Rights Reserved.

"""deployments stop command."""

from googlecloudsdk.core import log
from googlecloudsdk.core import properties

from apitools.base import py as apitools_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import list_printer
from googlecloudsdk.core.util import resource_printer
from googlecloudsdk.deployment_manager.lib import dm_v2_util

# Number of seconds (approximately) to wait for stop operation to complete.
OPERATION_TIMEOUT = 20 * 60  # 20 mins


class Stop(base.Command):
  """Stop a pending or running deployment update or creation.

  This command will stop a currently running or pending operation on
  a deployment.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To stop a running operation on a deployment, run:

            $ {command} my-deployment

          To issue a stop command without waiting for the operation to complete, run:

            $ {command} my-deployment --async
          """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        '--async',
        help='Return immediately and print information about the Operation in '
        'progress rather than waiting for the Operation to complete. '
        '(default=False)',
        default=False,
        action='store_true')

    parser.add_argument('deployment_name', help='Deployment name.')

  def Run(self, args):
    """Run 'deployments stop'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If --async=true, returns Operation to poll.
      Else, returns boolean indicating whether stop operation succeeded.

    Raises:
      HttpException: An http error response was received while executing api
          request.
      ToolException: The stop operation encountered an error.
    """
    client = self.context['deploymentmanager-client']
    messages = self.context['deploymentmanager-messages']
    project = properties.VALUES.core.project.Get(required=True)

    # Get the fingerprint from the deployment to stop.
    try:
      current_deployment = client.deployments.Get(
          messages.DeploymentmanagerDeploymentsGetRequest(
              project=project,
              deployment=args.deployment_name
          )
      )
      # If no fingerprint is present, default to an empty fingerprint.
      # This empty default can be removed once the fingerprint change is
      # fully implemented and all deployments have fingerprints.
      fingerprint = current_deployment.fingerprint or ''
    except apitools_base.HttpError as error:
      raise exceptions.HttpException(dm_v2_util.GetError(error))

    try:
      operation = client.deployments.Stop(
          messages.DeploymentmanagerDeploymentsStopRequest(
              project=project,
              deployment=args.deployment_name,
              deploymentsStopRequest=messages.DeploymentsStopRequest(
                  fingerprint=fingerprint,
              ),
          )
      )
    except apitools_base.HttpError as error:
      raise exceptions.HttpException(dm_v2_util.GetError(error))
    if args.async:
      return operation
    else:
      op_name = operation.name
      try:
        dm_v2_util.WaitForOperation(op_name, project, self.context, 'stop',
                                    OPERATION_TIMEOUT)
        log.status.Print('Stop operation ' + op_name
                         + ' completed successfully.')
      except exceptions.ToolException:
        # Operation timed out or had errors. Print this warning, then still
        # show whatever operation can be gotten.
        log.error('Stop operation ' + op_name
                  + ' has errors or failed to complete within '
                  + str(OPERATION_TIMEOUT) + ' seconds.')
      except apitools_base.HttpError as error:
        raise exceptions.HttpException(dm_v2_util.GetError(error))
      try:
        # Fetch a list of the stopped resources.
        response = client.resources.List(
            messages.DeploymentmanagerResourcesListRequest(
                project=project,
                deployment=args.deployment_name,
            )
        )
        # TODO(user): Pagination
        return response.resources if response.resources else []
      except apitools_base.HttpError as error:
        raise exceptions.HttpException(dm_v2_util.GetError(error))

  def Display(self, unused_args, result):
    """Display prints information about what just happened to stdout.

    Args:
      unused_args: The same as the args in Run.

      result: an Operation (may be in progress or completed) to display
          or a list of Resources, if a synchronous stop completed
          successfully.

    Raises:
      ValueError: if result is None or not a dict
    """
    messages = self.context['deploymentmanager-messages']
    if isinstance(result, messages.Operation):
      resource_printer.Print(resources=result,
                             print_format=unused_args.format or 'yaml',
                             out=log.out)
    elif isinstance(result, list) and (
        not result or isinstance(result[0], messages.Resource)):
      list_printer.PrintResourceList('deploymentmanagerv2.resources',
                                     result)
    else:
      raise ValueError('result must be an Operation or list of Resources')

