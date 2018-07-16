# Copyright 2013 Google Inc. All Rights Reserved.

"""The Delete command."""

from googlecloudsdk.appengine.lib import appengine_client
from googlecloudsdk.appengine.lib import flags
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io


class Delete(base.Command):
  """Delete a specific version of the given modules.

  This command deletes the specified version of the given modules from the
  App Engine server.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To delete a single module, run:

            $ {command} default --version=1

          To delete multiple modules, run:

            $ {command} module1 module2 --version=1
          """,
  }

  @staticmethod
  def Args(parser):
    flags.SERVER_FLAG.AddToParser(parser)
    flags.VERSION_FLAG.AddToParser(parser)
    flags.MODULES_ARG.AddToParser(parser)

  def Run(self, args):
    client = appengine_client.AppengineClient(args.server)

    message = 'You are about to delete the following module versions:\n\t'
    message += '\n\t'.join(
        ['{0}/{1}/{2}'.format(client.project, m, args.version)
         for m in args.modules])
    console_io.PromptContinue(message=message, cancel_on_no=True)

    # Will run client.DeleteModule on each module with the specified version.
    # In event of a failure, will still attempt to delete the remaining modules.
    # Prints out a warning or error as appropriate for each module deletion.
    delete_results = []
    for module in args.modules:
      delete_results.append(client.DeleteModule(module, args.version))
    if not all(delete_results):
      raise exceptions.ToolException('Not all deletions succeeded.')
