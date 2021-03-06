# Copyright 2013 Google Inc. All Rights Reserved.

"""Command to print version information for Cloud SDK components.
"""

import textwrap

from googlecloudsdk.core import config
from googlecloudsdk.core import log

from googlecloudsdk.calliope import base
from googlecloudsdk.core.updater import update_manager


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Version(base.Command):
  """Print version information for Cloud SDK components.

     This command prints version information for each installed Cloud SDK
     component and prints a message if updates are available.
  """

  def Run(self, args):
    if config.Paths().sdk_root:
      # Components are only valid if this is a built Cloud SDK.
      manager = update_manager.UpdateManager()
      return manager.GetCurrentVersionsInformation()
    return []

  def Display(self, args, result):
    printables = []
    for name in sorted(result):
      version = result[name]
      printables.append('{name} {version}'.format(name=name, version=version))
    component_versions = '\n'.join(printables)
    log.Print(textwrap.dedent("""\
Google Cloud SDK {cloudsdk_version}

{component_versions}
""".format(
    cloudsdk_version=config.CLOUD_SDK_VERSION,
    component_versions=component_versions)))
