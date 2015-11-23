
# Copyright 2013 Google Inc. All Rights Reserved.

"""Utility methods used by the deploy command."""

import os
import re

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.docker import constants

from googlecloudsdk.appengine.lib.external.api import appinfo
from googlecloudsdk.appengine.lib import util
from googlecloudsdk.appengine.lib.docker import containers
from googlecloudsdk.appengine.lib.images import docker_util
from googlecloudsdk.appengine.lib.images import push

from googlecloudsdk.core import metrics
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.docker import docker


DEFAULT_DOMAIN = 'appspot.com'
DEFAULT_MODULE = 'default'
DEFAULT_MODULE = 'default'
ALT_SEPARATOR = '-dot-'
MAX_DNS_LABEL_LENGTH = 63  # http://tools.ietf.org/html/rfc2181#section-11

# Wait this long before displaying an additional message
_PREPARE_VM_MESSAGE_DELAY = 15

# Metric names for CSI
_REMOTE_BUILD = 'remote_build'
_BUILD = 'build'


def BuildAndPushDockerImages(module_configs, version_id, client, cli, remote,
                             implicit_remote_build):
  # PrepareVmRuntime only needs to be called once per deployment.
  project = properties.VALUES.core.project.Get(required=True)

  if any(info.RequiresImage() for info in module_configs.values()):
    log.status.Print('Verifying that Managed VMs are enabled and ready.')
    message = 'If this is your first deployment, this may take a while'
    try:
      with console_io.DelayedProgressTracker(message,
                                             _PREPARE_VM_MESSAGE_DELAY):
        client.PrepareVmRuntime()
      log.status.Print()
    except util.RPCError as err:
      log.warn('If this is your first deployment, please try again.')
      raise err

    for registry in constants.ALL_SUPPORTED_REGISTRIES:
      docker.UpdateDockerCredentials(registry)

    if remote and implicit_remote_build:
      # Test for presence of local Docker
      try:
        with docker_util.DockerHost(cli, version_id, False) as docker_client:
          if os.environ.get('DOCKER_HOST'):
            docker_client.ping()
            log.warn('A hosted build is being performed, but a local Docker '
                     'was found. Specify `--docker-build=local` to use it, or '
                     '`--docker-build=remote` to silence this warning.')
      except containers.DockerDaemonConnectionError:
        pass

    with docker_util.DockerHost(cli, version_id, remote) as docker_client:
      # Build and push all images.
      for (module, info) in module_configs.iteritems():
        if info.RequiresImage():
          log.status.Print(
              'Building and pushing image for module [{module}]'
              .format(module=module))
          info.UpdateManagedVMConfig()
          push.BuildAndPushDockerImage(info.file, project, module, version_id,
                                       info.runtime, docker_client)
    metric_name = _REMOTE_BUILD if remote else _BUILD
    metrics.CustomTimedEvent(metric_name)


def UseSsl(handlers):
  for handler in handlers:
    try:
      if re.match(handler.url + '$', '/'):
        return handler.secure
    except re.error:
      # AppEngine uses POSIX Extended regular expressions, which are not 100%
      # compatible with Python's re module.
      pass
  return appinfo.SECURE_HTTP


def GetAppHostname(app_id, module=None, version=None,
                   use_ssl=appinfo.SECURE_HTTP):
  if not app_id:
    msg = 'Must provide a valid app ID to construct a hostname.'
    raise exceptions.Error(msg)
  version = version or ''
  module = module or ''
  if module == DEFAULT_MODULE:
    module = ''

  domain = DEFAULT_DOMAIN
  if ':' in app_id:
    domain, app_id = app_id.split(':')

  if module == DEFAULT_MODULE:
    module = ''

  # Normally, AppEngine URLs are of the form
  # 'http[s]://version.module.app.appspot.com'. However, the SSL certificate for
  # appspot.com is not valid for subdomains of subdomains of appspot.com (e.g.
  # 'https://app.appspot.com/' is okay; 'https://module.app.appspot.com/' is
  # not). To deal with this, AppEngine recognizes URLs like
  # 'http[s]://version-dot-module-dot-app.appspot.com/'.
  #
  # This works well as long as the domain name part constructed in this fashion
  # is less than 63 characters long, as per the DNS spec. If the domain name
  # part is longer than that, we are forced to use the URL with an invalid
  # certificate.
  #
  # We've tried to do the best possible thing in every case here.
  subdomain_parts = filter(bool, [version, module, app_id])
  scheme = 'http'
  if use_ssl == appinfo.SECURE_HTTP:
    subdomain = '.'.join(subdomain_parts)
    scheme = 'http'
  else:
    subdomain = ALT_SEPARATOR.join(subdomain_parts)
    if len(subdomain) <= MAX_DNS_LABEL_LENGTH:
      scheme = 'https'
    else:
      subdomain = '.'.join(subdomain_parts)
      if use_ssl == appinfo.SECURE_HTTP_OR_HTTPS:
        scheme = 'http'
      elif use_ssl == appinfo.SECURE_HTTPS:
        msg = ('Most browsers will reject the SSL certificate for module {0}. '
               'Please verify that the certificate corresponds to the parent '
               'domain of your application when you connect.').format(module)
        log.warn(msg)
        scheme = 'https'

  return '{0}://{1}.{2}'.format(scheme, subdomain, domain)
