# Copyright 2013 Google Inc. All Rights Reserved.

"""The cancel-deployment command."""

from googlecloudsdk.appengine.lib import appengine_client
from googlecloudsdk.appengine.lib import flags
from googlecloudsdk.calliope import base


class CancelDeployment(base.Command):
  """Cancel an in progress or hung deployment of the given modules.

  This command cancels an in progress or hung deployment of the given modules.
  This command should only be necessary when a deployment fails and a subsequent
  one cannot be started.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To cancel a deployment, run:

            $ {command} default --version=1

          To cancel multiple deployments, run:

            $ {command} module1 module2 --version=1
          """,
  }

  @staticmethod
  def Args(parser):
    flags.SERVER_FLAG.AddToParser(parser)
    flags.VERSION_FLAG.AddToParser(parser)
    flags.MODULES_ARG.AddToParser(parser)

  def Run(self, args):
    client = appengine_client.AppengineClient(args.server)
    for module in args.modules:
      client.CancelDeployment(module, args.version)
