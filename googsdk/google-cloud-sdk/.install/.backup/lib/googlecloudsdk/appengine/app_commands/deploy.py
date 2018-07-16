
# Copyright 2013 Google Inc. All Rights Reserved.

"""The gcloud app deploy command."""

import argparse

from googlecloudsdk.core import log
from googlecloudsdk.core import properties

from googlecloudsdk.appengine.lib import appengine_api_client
from googlecloudsdk.appengine.lib import appengine_client
from googlecloudsdk.appengine.lib import cloud_storage
from googlecloudsdk.appengine.lib import deploy_app_command_util
from googlecloudsdk.appengine.lib import deploy_command_util
from googlecloudsdk.appengine.lib import flags
from googlecloudsdk.appengine.lib import util
from googlecloudsdk.appengine.lib import yaml_parsing
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io

DEPLOY_MESSAGE_TEMPLATE = """\
{project}/{module} (from [{file}])
     Deployed URL: [{url}]
"""
SET_DEFAULT_MESSAGE = """\
     (add --set-default if you also want to make this module available from
     [{default_url}])
"""


def _DisplayProposedDeployment(project, app_config, version, set_default):
  """Prints the details of the proposed deployment.

  Args:
    project: the name of the current project
    app_config: the application configuration to be deployed
    version: the version identifier of the application to be deployed
    set_default: whether the newly deployed version will be set as the default
        version (this affects deployed URLs)

  Returns:
    dict (str->str), a mapping of module names to deployed module URLs

  This includes information on to-be-deployed modules (including module name,
  version number, and deployed URLs) as well as configurations.
  """
  # TODO(user): Have modules and configs be able to print themselves.  We
  # do this right now because we actually need to pass a yaml file to appcfg.
  # Until we can make a call with the correct values for project and version
  # it is weird to override those values in the yaml parsing code (because
  # it does not carry through to the actual file contents).
  deployed_urls = {}
  if app_config.Modules():
    printer = console_io.ListPrinter(
        'You are about to deploy the following modules:')
    deploy_messages = []
    for module, info in app_config.Modules().iteritems():
      use_ssl = deploy_command_util.UseSsl(info.parsed.handlers)
      version = None if set_default else version
      url = deploy_command_util.GetAppHostname(
          project, module=info.module, version=version, use_ssl=use_ssl)
      deployed_urls[module] = url
      deploy_message = DEPLOY_MESSAGE_TEMPLATE.format(
          project=project, module=module, file=info.file, url=url)
      if not set_default:
        default_url = deploy_command_util.GetAppHostname(
            project, module=info.module, use_ssl=use_ssl)
        deploy_message += SET_DEFAULT_MESSAGE.format(default_url=default_url)
      deploy_messages.append(deploy_message)
    printer.Print(deploy_messages, output_stream=log.status)

  if app_config.Configs():
    printer = console_io.ListPrinter(
        'You are about to deploy the following configurations:')
    printer.Print(
        ['{0}/{1}  (from [{2}])'.format(project, c.config, c.file)
         for c in app_config.Configs().values()], output_stream=log.status)

  return deployed_urls


class Deploy(base.Command):
  """Deploy the local code and/or configuration of your app to App Engine.

  This command is used to deploy both code and configuration to the App Engine
  server.  As an input it takes one or more ``DEPLOYABLES'' that should be
  uploaded.  A ``DEPLOYABLE'' can be a module's .yaml file or a configuration's
  .yaml file.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To deploy a single module, run:

            $ {command} ~/my_app/app.yaml

          To deploy multiple modules, run:

            $ {command} ~/my_app/app.yaml ~/my_app/another_module.yaml
          """,
  }

  @staticmethod
  def Args(parser):
    """Get arguments for this command.

    Args:
      parser: argparse.ArgumentParser, the parser for this command.
    """
    flags.SERVER_FLAG.AddToParser(parser)
    parser.add_argument(
        '--version',
        help='The version of the app that will be created or replaced by this '
        'deployment.  If you do not specify a version, one will be generated '
        'for you.')
    parser.add_argument(
        '--env-vars',
        help='Environment variable overrides for your app.')
    parser.add_argument(
        '--force',
        action='store_true',
        help=('Force deploying, overriding any previous in-progress '
              'deployments to this version.'))
    parser.add_argument(
        '--set-default',
        action='store_true',
        help='Set the deployed version to be the default serving version.')
    parser.add_argument(
        '--bucket',
        type=cloud_storage.GcsBucketArgument,
        help=argparse.SUPPRESS)
    docker_build_group = parser.add_mutually_exclusive_group()
    docker_build_group.add_argument(
        '--docker-build',
        choices=['remote', 'local'],
        default=None,
        help=("Perform a hosted ('remote') or local Docker build. To perform a "
              "local build, you must have your local docker environment "
              "configured correctly. The default is  a hosted build."))
    parser.add_argument(
        'deployables', nargs='+',
        help='The yaml files for the modules or configurations you want to '
        'deploy.')

  @property
  def use_admin_api(self):
    return properties.VALUES.app.use_appengine_api.GetBool()

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)

    api_client = None
    if self.use_admin_api:
      api_client = appengine_api_client.GetApiClient(self.Http(timeout=None))
      log.debug('API endpoint: [{endpoint}], API version: [{version}]'.format(
          endpoint=api_client.client.url,
          version=api_client.api_version))

    if self.use_admin_api and not args.bucket:
      # TODO(user) Default to an appspot bucket. Requires other work on the
      # Cloud Integration side first.
      # For now, this argument is required.
      raise exceptions.RequiredArgumentException(
          'bucket',
          ('A Google Cloud Storage bucket is required when deploying using the '
           'App Engine API.'))

    # remote_build indicates that the deployment should use a hosted Docker
    # build; implicit_remote_build indicates that remote_build is True (the
    # default) and was not specified by either a command line flag or a
    # property. This indicates that the deployment should warn if a local Docker
    # environment is found.
    remote_build = True
    implicit_remote_build = True
    docker_build_property = properties.VALUES.app.docker_build.Get()
    if args.docker_build:
      remote_build = args.docker_build == 'remote'
      implicit_remote_build = False
    elif docker_build_property:
      remote_build = docker_build_property == 'remote'
      implicit_remote_build = False

    app_config = yaml_parsing.AppConfigSet(
        args.deployables, project, args.version or util.GenerateVersionId())
    # This will either be args.version or a generated version.  Either way, if
    # any yaml file has a version in it, it must match that version.
    version = app_config.Version()

    client = appengine_client.AppengineClient(args.server)

    deployed_urls = _DisplayProposedDeployment(project, app_config, version,
                                               args.set_default)
    if args.version or args.set_default:
      # Prompt if there's a chance that you're overwriting something important:
      # If the version is set manually, you could be deploying over something.
      # If you're setting the new deployment to be the default version, you're
      # changing the target of the default URL.
      # Otherwise, all existing URLs will continue to work, so need to prompt.
      console_io.PromptContinue(default=True, throw_if_unattended=False,
                                cancel_on_no=True)

    log.status.Print('Beginning deployment...')

    # Fall back to a remote build if the local build fails and was done
    # implicitly.
    deploy_command_util.BuildAndPushDockerImages(app_config.Modules(),
                                                 version,
                                                 client,
                                                 self.cli,
                                                 remote_build,
                                                 implicit_remote_build)

    deployment_manifests = {}
    if self.use_admin_api and app_config.Modules():
      # TODO(user): Consider doing this in parallel with
      # BuildAndPushDockerImage.
      log.status.Print('Copying files to Google Cloud Storage...')
      deployment_manifests = deploy_app_command_util.CopyFilesToCodeBucket(
          app_config.Modules().items(), args.bucket)

    for (module, info) in app_config.Modules().iteritems():
      message = 'Updating module [{module}]'.format(module=module)
      with console_io.ProgressTracker(message):
        if args.force:
          client.CancelDeployment(module=module, version=version)

        # TODO(user): Pass args.env_vars through to appcfg update.
        # TODO(user): Pass args.env_vars through to DeployModule.
        if self.use_admin_api:
          api_client.DeployModule(module, version, info,
                                  deployment_manifests[module])
        else:
          client.DeployModule(module, version, info.parsed, info.file)

        if args.set_default:
          if self.use_admin_api:
            api_client.SetDefaultVersion(module, version)
          else:
            client.SetDefaultVersion(modules=[module], version=version)

    # Config files.
    for (c, info) in app_config.Configs().iteritems():
      message = 'Updating config [{config}]'.format(config=c)
      with console_io.ProgressTracker(message):
        client.UpdateConfig(c, info.parsed)
    return deployed_urls

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    writer = log.out
    for module, url in result.items():
      writer.Print('Deployed module [{0}] to [{1}]'.format(module, url))
