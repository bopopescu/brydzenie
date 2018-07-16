# Copyright 2015 Google Inc. All Rights Reserved.

"""The gen-config command."""

import os

from googlecloudsdk.appengine.lib.runtimes import fingerprinter
from googlecloudsdk.calliope import base


class GenConfig(base.Command):
  """Generate missing configuration files for a source directory.

  This command generates all relevant config files (app.yaml, Dockerfile and a
  build Dockerfile) for your application in the current directory or emits an
  error message if the source directory contents are not recognized.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To generate configs for the current directory:

            $ {command}

          To generate configs for ~/my_app:

            $ {command} ~/my_app
          """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'source_dir',
        nargs='?',
        help='The source directory to fingerprint.',
        default=os.getcwd())

  def Run(self, args):
    fingerprinter.GenerateConfigs(args.source_dir)
