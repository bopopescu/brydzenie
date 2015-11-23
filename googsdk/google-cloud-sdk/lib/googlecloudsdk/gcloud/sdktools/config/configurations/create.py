# Copyright 2015 Google Inc. All Rights Reserved.

"""Command to create named configuration."""

from googlecloudsdk.core import log
from googlecloudsdk.core import named_configs

from googlecloudsdk.calliope import base


class Create(base.Command):
  """Creates a new named configuration and activates it.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To create and activate a new named configuration, run:

            $ {command} my_config

          To list all properties in the new configuration, run:

            $ gcloud config list -all
          """,
  }

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        'configuration_name',
        help='Configuration name to create')

  def Run(self, args):
    named_configs.CreateNamedConfig(args.configuration_name)
    named_configs.ActivateNamedConfig(args.configuration_name)

    log.CreatedResource(args.configuration_name)
    log.status.write('Activated [{0}].\n'.format(args.configuration_name))
    return args.configuration_name
