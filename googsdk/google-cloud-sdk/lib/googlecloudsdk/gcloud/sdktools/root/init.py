# Copyright 2014 Google Inc. All Rights Reserved.

"""Initialize a gcloud workspace.

Creates a .gcloud folder. When gcloud starts, it looks for this .gcloud folder
in the cwd or one of the cwd's ancestors.
"""

import argparse
import os
import sys
import textwrap

from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import workspaces
from googlecloudsdk.core.util import files

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import store as c_store


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Init(base.Command):
  """Create and initialize a gcloud workspace in the current directory."""

  detailed_help = {
      'DESCRIPTION': """\
          This command creates and initializes a local workspace for a Google
          Cloud Platform project.

          The local workspace is indicated by the creation of a [{dotgcloud}]
          folder. In this folder is a file [properties] which allows you to
          override any global properties you may have set via the
          `$ gcloud config` command.

          When you run a Cloud SDK command-line tool from within this new
          workspace, it will use the new [properties] file as the first place to
          load properties. As a result, if you use gcloud, bq, gsutil, or
          any of the other commands in google-cloud-sdk/bin from within the
          workspace, they will connect to the correct project.

          If you have enabled push-to-deploy in the Cloud Console, one of the
          things that `gcloud init` will do for you is cloning the Google-hosted
          git repository associated with PROJECT. This repository will
          automatically be connected to Google, and it will use the credentials
          indicated as _active_ by `gcloud auth list`. Pushing
          to the origin's _main_ branch will trigger an App Engine deployment
          using the contents of that branch.

          **Note: this command will be changing soon. Consider using
          `$ gcloud alpha source clone` to clone authenticated git repository.
      """.format(dotgcloud=config.Paths.CLOUDSDK_WORKSPACE_CONFIG_DIR_NAME),
      'EXAMPLES': textwrap.dedent("""\
          To perform a simple `"Hello, world!"` App Engine deployment with this
          command, run the following command lines with MYPROJECT replaced by
          a project you own and can use for this experiment.

            $ gcloud auth login
            $ gcloud init MYPROJECT
            $ cd MYPROJECT/default
            $ git pull
              https://github.com/GoogleCloudPlatform/appengine-helloworld-python
            $ git push origin main
      """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--devshell-image',
        help=argparse.SUPPRESS,
        required=False)
    project_arg = parser.add_argument(
        'project',
        help='The Google Cloud project to tie the workspace to.')
    project_arg.detailed_help = """\
        The name of the Google Cloud Platform project that you want to use in a
        local workspace that will be created by this command. If this project
        has an associated Google-hosted git repository, that repository will be
        cloned into the local workspace.
        """

  @c_exc.RaiseToolExceptionInsteadOf(workspaces.Error, c_store.Error)
  def Run(self, args):
    """Create the .gcloud folder, if possible.

    Args:
      args: argparse.Namespace, the arguments this command is run with.

    Raises:
      ToolException: on project initialization errors.

    Returns:
      The path to the new gcloud workspace.
    """
    log.warn('`gcloud init` will be changing soon. '
             'To clone git repo consider using `gcloud alpha source repo clone`'
             ' command.')
    # Ensure that we're logged in.
    c_store.Load()

    is_new_directory = False

    try:
      workspace = workspaces.FromCWD()
      # Cannot re-init when in a workspace.
      current_project = workspace.GetProperty(properties.VALUES.core.project)
      if current_project != args.project:
        message = (
            'Directory [{root_directory}] is already initialized to project'
            ' [{project}].'
        ).format(
            root_directory=workspace.root_directory,
            project=current_project)
      else:
        message = (
            'Directory [{root_directory}] is already initialized.'
        ).format(root_directory=workspace.root_directory)
      raise c_exc.ToolException(message)
    except workspaces.NoContainingWorkspaceException:
      workspace_dir = os.path.join(os.getcwd(), args.project)
      message = (
          'Directory [{root_directory}] is not empty.'
      ).format(root_directory=workspace_dir)
      if os.path.exists(workspace_dir) and os.listdir(workspace_dir):
        raise c_exc.ToolException(message)
      else:
        files.MakeDir(workspace_dir)
        is_new_directory = True
        workspace = workspaces.Create(workspace_dir)

    workspace.SetProperty(properties.VALUES.core.project, args.project)
    if args.devshell_image:
      workspace.SetProperty(properties.VALUES.devshell.image,
                            args.devshell_image)

    # Everything that can fail should happen within this next try: block.
    # If something fails, and the result is an empty directory that we just
    # created, we clean it up.
    try:
      workspace.CloneProjectRepository(
          args.project, workspaces.DEFAULT_REPOSITORY_ALIAS)
    except workspaces.CannotFetchRepositoryException as e:
      log.error(e)
    finally:
      cleared_files = False
      if is_new_directory:
        dir_files = os.listdir(workspace_dir)
        if not dir_files or dir_files == [
            config.Paths().CLOUDSDK_WORKSPACE_CONFIG_DIR_NAME]:
          log.error(('Unable to initialize project [{project}], cleaning up'
                     ' [{path}].').format(
                         project=args.project, path=workspace_dir))
          files.RmTree(workspace_dir)
          cleared_files = True
    if cleared_files:
      raise c_exc.ToolException(
          'Unable to initialize project [{project}].'.format(
              project=args.project))
    log.status.write('Project [{prj}] was initialized in [{path}].\n'.format(
        path=workspace.root_directory,
        prj=args.project))

    return workspace


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class InitAlpha(base.Command):
  """Workflow to set up gcloud environment."""

  detailed_help = {
      'DESCRIPTION': """\
          This command configures gcloud for a Google Cloud Platform project.

          It runs interactive session for the user guiding through the setup
          process.
      """,
  }

  @staticmethod
  def Args(parser):
    pass

  def Run(self, args):
    """Allows user to select configuration, and initialize it."""

    log.status.write('Welcome! This command will take you through '
                     'the configuration of gcloud.\n\n')

    configuration_name = None
    try:
      configuration_name = self._PickConfiguration()
      if not configuration_name:
        return
      log.status.write('Your current configuration is set to: [{0}]\n\n'
                       .format(configuration_name))

      if not self._PickAccount():
        return

      if not self._PickProject():
        return

      self._PickDefaultRegionAndZone()

      self._PickRepo()

      log.status.write('\ngcloud has now been configured!\n')
    finally:
      log.status.write('You can use [gcloud config] to '
                       'change more gcloud settings.\n\n')
      if configuration_name:
        log.status.write('Your current configuration is: [{0}]\n\n'
                         .format(configuration_name))
      log.status.flush()

      # Not using self._RunCmd to get command actual output.
      self.cli.Execute(['config', 'list'])

  def _PickAccount(self):
    """Checks if current credentials are valid, if not runs auth login.

    Returns:
      bool, True if valid credentials are setup.
    """

    auth_info = self._RunCmd(['auth', 'list'])
    if auth_info and auth_info.accounts:
      idx = console_io.PromptChoice(
          auth_info.accounts + ['Login with new credentials'],
          message='Pick credentials to use:',
          prompt_string=None)
      if idx is None:
        return None
      new_credentials = idx == len(auth_info.accounts)
    else:
      answer = console_io.PromptContinue(
          prompt_string='To continue, you must login. Would you like to login')
      if not answer:
        return False
      new_credentials = True
    if new_credentials:
      # gcloud auth login may have user interaction, do not suppress it.
      self._RunCmd(['auth', 'login'], disable_user_output=False)
    else:
      account = auth_info.accounts[idx]
      self._RunCmd(['config', 'set'], ['account', account])

    log.status.write('\nYou are now logged in as: [{0}]\n'
                     .format(properties.VALUES.core.account.Get()))
    return True

  def _PickConfiguration(self):
    """Allows user to re-initialize, create or pick new configuration.

    Returns:
      Configuration name or None.
    """

    configs = self._RunCmd(['alpha', 'config', 'configurations', 'list'])
    if not configs:
      new_config_name = 'default'
      if self._RunCmd(['alpha', 'config', 'configurations',
                       'create'], [new_config_name]):
        properties.PropertiesFile.Invalidate()
      return new_config_name

    config_names = [cfg.name for cfg in configs]
    active_configs = [cfg.name for cfg in configs
                      if getattr(cfg, 'is_active', False)]
    if not active_configs:
      return None
    choices = []
    active_config = active_configs[0]
    choices.append(
        'Re-initialize this configuration [{0}] with new settings '
        '(current settings will be lost)'.format(active_config))
    choices.append('Create a new configuration')
    config_choices = [name for name in config_names if name != active_config]
    choices.extend('Switch to existing configuration: [{0}]'.format(name)
                   for name in config_choices)
    idx = console_io.PromptChoice(
        choices, message='Please select from the following choices:',
        prompt_string=None)
    if idx is None:
      return None
    if idx == 0:  # If reinitialize was selected.
      self._CleanCurrentConfiguration()
      return active_config
    if idx == 1:  # Second option is to create new configuration.
      return self._CreateConfiguration()
    config_name = config_choices[idx - 2]
    self._RunCmd(['alpha', 'config', 'configurations', 'activate'],
                 [config_name])
    return config_name

  def _PickProject(self):
    """Allows user to select a project.

    Returns:
      str, project_id or None if was not selected.
    """
    projects = self._RunCmd(['alpha', 'projects', 'list'])
    if projects is None:  # Failed to get the list.
      project_id = console_io.PromptResponse(
          'Enter project id you would like to use: ')
      if not project_id:
        return None
    else:
      projects = sorted(projects, key=lambda prj: prj.projectId)
      choices = ['[{0}]'.format(project.projectId) for project in projects]
      if not choices:
        log.status.write('\nThis account has no projects. Please create one in '
                         'developers console '
                         '(https://console.developers.google.com/project) '
                         'before running this command.\n')
        return None
      if len(choices) == 1:
        project_id = projects[0].projectId
      else:
        idx = console_io.PromptChoice(
            choices,
            message='\nWhich of your cloud projects do you want to use:',
            prompt_string=None)
        if idx is None:
          return
        project_id = projects[idx].projectId

    self._RunCmd(['config', 'set'], ['project', project_id])
    log.status.write('Your current project is set to: [{0}].\n'
                     .format(project_id))
    return project_id

  def _PickDefaultRegionAndZone(self):
    """Pulls metadata properties for region and zone and sets them in gcloud."""
    project_info = self._RunCmd(['compute', 'project-info', 'describe'])
    default_zone = None
    default_region = None
    if project_info is not None:
      metadata = project_info.get('commonInstanceMetadata', {})
      for item in metadata.get('items', []):
        if item['key'] == 'google-compute-default-zone':
          default_zone = item['value']
        elif item['key'] == 'google-compute-default-region':
          default_region = item['value']

    # Same logic applies to region and zone properties.
    def SetProperty(name, default_value, list_command):
      """Set named compute property to default_value or get via list command."""
      if default_value:
        log.status.write('\nYour project default compute {0} is set to [{1}].\n'
                         'You can change it by running '
                         '[gcloud config set compute/{0} NAME].\n'
                         .format(name, default_value['name']))
      else:
        values = self._RunCmd(list_command)
        if values is None:
          return
        values = list(values)
        idx = console_io.PromptChoice(
            ['[{0}]'.format(value['name']) for value in values]
            + ['Do not set default {0}'.format(name)],
            message=('Which compute {0} would you like '
                     'to use as project default?'.format(name)),
            prompt_string=None)
        if idx is None or idx == len(values):
          return
        default_value = values[idx]
      self._RunCmd(['config', 'set'],
                   ['compute/{0}'.format(name), default_value['name']])
      log.status.write(
          'Set default {0} to [{1}]\n'.format(name, default_value['name']))
      return default_value

    if default_zone:
      default_zone = self._RunCmd(['compute', 'zones', 'describe'],
                                  [default_zone])
    zone = SetProperty('zone', default_zone, ['compute', 'zones', 'list'])
    if zone and not default_region:
      default_region = zone['region']
    if default_region:
      default_region = self._RunCmd(['compute', 'regions', 'describe'],
                                    [default_region])
    SetProperty('region', default_region, ['compute', 'regions', 'list'])

  def _PickRepo(self):
    """Allows user to clone one of the projects repositories."""
    repos = self._RunCmd(['alpha', 'source', 'repo', 'list'])
    if repos:
      repos = sorted(repo.name or 'default' for repo in repos)
      log.status.write(
          '\nThis project has one or more associated git repositories.\n')
      idx = console_io.PromptChoice(
          ['[{0}]'.format(repo) for repo in repos] + ['Do not clone'],
          message='Which one you want gcloud to clone to your local machine?',
          prompt_string=None)
      if idx < len(repos):
        repo_name = repos[idx]
        self._CloneRepo(repo_name)

  def _CloneRepo(self, repo_name):
    """Queries user for output path and clones selected repo to it."""
    while True:
      clone_path = os.getcwd()
      clone_path = console_io.PromptResponse(
          'Where would you like to clone [{0}] repository to [{1}]:'
          .format(repo_name, clone_path))
      if not clone_path:
        clone_path = os.getcwd()
      if os.path.isdir(clone_path):
        break
      log.status.write('No such directory [{0}]\n'.format(clone_path))

    self._RunCmd(['alpha', 'source', 'repo', 'clone'],
                 [repo_name, os.path.join(clone_path, repo_name)])

  def _CreateConfiguration(self):
    configuration_name = console_io.PromptResponse('Enter configuration name:')
    new_config_name = self._RunCmd([
        'alpha', 'config', 'configurations', 'create'], [configuration_name])
    if new_config_name:
      properties.PropertiesFile.Invalidate()
    return new_config_name

  def _CleanCurrentConfiguration(self):
    self._RunCmd(['config', 'unset'], ['account'])
    self._RunCmd(['config', 'unset'], ['project'])
    self._RunCmd(['config', 'unset'], ['compute/zone'])
    self._RunCmd(['config', 'unset'], ['compute/region'])

  def _RunCmd(self, cmd, params=None, disable_user_output=True):
    if not self.cli.IsValidCommand(cmd):
      log.info('Command %s does not exist.', cmd)
      return None
    if params is None:
      params = []
    args = cmd + params
    log.info('Executing: [gcloud %s]', ' '.join(args))
    try:
      # Disable output from individual commands, so that we get
      # command run results, and don't clutter output of init.
      if disable_user_output:
        args.append('--user-output-enabled=false')

      if (properties.VALUES.core.verbosity.Get() is None and
          disable_user_output):
        # Unless user explicitly set verbosity, suppress from subcommands.
        args.append('--verbosity=none')

      return self.cli.Execute(args)
    except (Exception, SystemExit):  # pylint:disable=broad-except
      log.status.write('Failed to run [{0}]\n'.format(' '.join(cmd + params)))
      log.debug('Failed to execute %s, %s, %s, %s', args, *sys.exc_info())
      return None
