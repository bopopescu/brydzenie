# Copyright 2013 Google Inc. All Rights Reserved.

"""Common functionality to support source fingerprinting."""


class Configurator(object):
  """Base configurator class.

  Configurators generate config files for specific classes of runtimes.  They
  are returned by the Fingerprint functions in the runtimes sub-package after
  a successful match of the runtime's heuristics.
  """

  def GenerateConfigs(self):
    """Generate all configuration files for the module.

    Generates config files in the current working directory.
    """
    raise NotImplementedError()
