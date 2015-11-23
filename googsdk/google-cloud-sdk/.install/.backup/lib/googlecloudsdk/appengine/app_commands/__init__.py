# Copyright 2013 Google Inc. All Rights Reserved.

"""The gcloud app group."""

from googlecloudsdk.calliope import base


@base.Beta
class Appengine(base.Group):
  """Manage your App Engine app.

  This set of commands allows you to deploy your app, manage your existing
  deployments, and also run your app locally.  These commands replace their
  equivalents in the appcfg tool.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To run your app locally in the development application server, run:

            $ {command} run DEPLOYABLES

          To create a new deployment of one or more modules, run:

            $ {command} deploy DEPLOYABLES

          To list your existing deployments, run:

            $ {command} modules list

          To generate config files for your source directory:

            $ {command} gen-config
          """,
  }
