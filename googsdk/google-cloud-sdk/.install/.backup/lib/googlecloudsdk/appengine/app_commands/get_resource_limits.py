# Copyright 2013 Google Inc. All Rights Reserved.

"""The Get Resource Limits command."""


from googlecloudsdk.appengine.lib import appengine_client
from googlecloudsdk.appengine.lib import flags
from googlecloudsdk.calliope import base


class GetResourceLimits(base.Command):
  """View the resource limits for the given version of your app."""

  detailed_help = {
      'EXAMPLES': """\
          To get the resource limits for your app, run:

            $ {command} --version=1
          """,
  }

  @staticmethod
  def Args(parser):
    flags.SERVER_FLAG.AddToParser(parser)
    flags.VERSION_FLAG.AddToParser(parser)

  def Run(self, args):
    client = appengine_client.AppengineClient(args.server)
    return client.ResourceLimitsInfo(args.version)

  def Display(self, args, result):
    self.format(result)
