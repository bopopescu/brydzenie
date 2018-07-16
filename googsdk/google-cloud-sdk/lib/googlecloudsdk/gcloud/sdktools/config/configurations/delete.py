# Copyright 2015 Google Inc. All Rights Reserved.

"""Command to delete named configuration."""

from googlecloudsdk.core import log
from googlecloudsdk.core import named_configs

from googlecloudsdk.calliope import base


class Delete(base.Command):
  """Deletes named configuration if it was not activate.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To delete named configuration, run:

            $ {command} my_config

          To list get a list of existing configurations, run:

            $ gcloud config configurations list
          """,
  }

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        'configuration_name',
        help=('Configuration name to delete, '
              'can not be currently active configuration.'))

  def Run(self, args):
    named_configs.DeleteNamedConfig(args.configuration_name)
    log.DeletedResource(args.configuration_name)
