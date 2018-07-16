# Copyright 2015 Google Inc. All Rights Reserved.

"""Configurations command group."""

from googlecloudsdk.core import config
from googlecloudsdk.core import properties

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Configurations(base.Group):
  """Manage set of gcloud configurations."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
      """
  }

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    Args:
      context: {str:object}, A set of key-value pairs that can be used for
          common initialization among commands.
      args: argparse.Namespace: The same namespace given to the corresponding
          .Run() invocation.
    """
    pass
