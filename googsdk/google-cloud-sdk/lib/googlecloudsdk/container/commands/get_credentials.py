# Copyright 2015 Google Inc. All Rights Reserved.

"""Fetch cluster credentials."""
from googlecloudsdk.core import properties

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.container.lib import util


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class GetCredentials(base.Command):
  """DEPRECATED: command was moved to 'container clusters get-credentials'."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        '--cluster', '-n',
        help='The name of the cluster to issue commands to.',
        action=actions.StoreProperty(properties.VALUES.container.cluster))

  @exceptions.RaiseToolExceptionInsteadOf(util.Error)
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      util.Error: Always. Command is moved/deprecated.
    """
    raise util.Error("""\
This command has been moved. Please run

  $ {cmd_path} clusters get-credentials""".format(
      cmd_path=' '.join(args.command_path[:-1])))
