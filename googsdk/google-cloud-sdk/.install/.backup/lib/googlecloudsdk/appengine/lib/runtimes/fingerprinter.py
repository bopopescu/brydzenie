# Copyright 2015 Google Inc. All Rights Reserved.

"""Package containing fingerprinting for all runtimes.
"""

from googlecloudsdk.core import exceptions

from googlecloudsdk.appengine.lib.runtimes import nodejs

# TODO(user): add some runtimes to this.
RUNTIMES = [
    nodejs,
]


class UnidentifiedDirectoryError(exceptions.Error):
  """Raised when GenerateConfigs() can't identify the directory."""

  def __init__(self, path):
    """Constructor.

    Args:
      path: (basestring) Directory we failed to identify.
    """
    super(UnidentifiedDirectoryError, self).__init__(
        'Unrecognized directory type: [{}]'.format(path))
    self.path = path


def IdentifyDirectory(path):
  for runtime in RUNTIMES:
    configurator = runtime.Fingerprint(path)
    if configurator:
      return configurator
  return None


def GenerateConfigs(path):
  """Generate all config files for the path into the current directory.

  Args:
    path: (basestring) Root directory to identify.

  Raises:
    UnidentifiedDirectoryError: No runtime module matched the directory.
  """
  module = IdentifyDirectory(path)
  if not module:
    raise UnidentifiedDirectoryError(path)

  module.GenerateConfigs()
