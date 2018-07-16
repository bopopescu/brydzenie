# Copyright 2015 Google Inc. All Rights Reserved.

"""Docker image and docker container classes.

In Docker terminology image is a read-only layer that never changes.
Container is created once you start a process in Docker from an Image. Container
consists of read-write layer, plus information about the parent Image, plus
some additional information like its unique ID, networking configuration,
and resource limits.
For more information refer to http://docs.docker.io/.

Mapping to Docker CLI:
Image is a result of "docker build path/to/Dockerfile" command.
ImageOptions allows to pass parameters to these commands.

Versions 1.9 and 1.10 of docker remote API are supported.
"""

from collections import namedtuple
import json
import os
import re
import socket
import ssl
import sys


from docker import docker
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import platforms
import requests
from requests.packages import urllib3
from googlecloudsdk.appengine.lib.images import config

from googlecloudsdk.core.console import console_attr_os


# This suppresses a urllib3 warning. More info can be found here:
# https://urllib3.readthedocs.org/en/latest/security.html
urllib3.disable_warnings()

_SUCCESSFUL_BUILD_PATTERN = re.compile(r'Successfully built ([a-zA-Z0-9]{12})')

_STREAM = 'stream'

DEFAULT_LINUX_DOCKER_HOST = '/var/run/docker.sock'
DOCKER_CONNECTION_ERROR = 'Couldn\'t connect to the Docker daemon.'
DOCKER_CONNECTION_ERROR_LOCAL = (
    'If you would like to perform the docker build locally, please check '
    'whether the environment variables DOCKER_HOST, DOCKER_CERT_PATH and '
    'DOCKER_TLS_VERIFY are set correctly.\n'
    'With boot2docker, you can set them up by running:\n'
    '  boot2docker shellinit\n'
    'and executing the commands that boot2docker shows.')
# TODO(user): revisit this message when
# https://github.com/boot2docker/boot2docker-cli/issues/301 is fixed

# Use the default width for logs that don't necessarily go to the screen
DOCKER_OUTPUT_BEGIN = ' DOCKER BUILD OUTPUT '
DOCKER_OUTPUT_LINE_CHAR = '-'


class ImageOptions(namedtuple('ImageOptionsT',
                              ['dockerfile_dir', 'tag', 'nocache', 'rm'])):
  """Options for building Docker Images."""

  def __new__(cls, dockerfile_dir=None, tag=None, nocache=False, rm=True):
    """This method is redefined to provide default values for namedtuple.

    Args:
      dockerfile_dir: str, Path to the directory with the Dockerfile.
      tag: str, Repository name (and optionally a tag) to be applied to the
          image in case of successful build.
      nocache: boolean, True if cache should not be used when building the
          image.
      rm: boolean, True if intermediate images should be removed after a
          successful build. Default value is set to True because this is the
          default value used by "docker build" command.

    Returns:
      ImageOptions object.
    """
    return super(ImageOptions, cls).__new__(
        cls, dockerfile_dir=dockerfile_dir, tag=tag, nocache=nocache, rm=rm)


class ImageBuildError(exceptions.Error):
  """Image build related errors."""


class DockerDaemonConnectionError(exceptions.Error):
  """Raised if the docker client can't connect to the Docker daemon."""


class Image(object):
  """Docker image that requires building and should be removed afterwards."""

  def __init__(self, docker_client, image_opts):
    """Initializer for Image.

    Args:
      docker_client: an object of docker.Client class to communicate with a
          Docker daemon.
      image_opts: an instance of ImageOptions class that must have
          dockerfile_dir set. image_id will be returned by "docker build"
          command.
    """
    self._docker_client = docker_client
    self._image_opts = image_opts
    self._id = None

  @property
  def id(self):
    """Returns 64 hexadecimal digit string identifying the image."""
    # Might also be a first 12-characters shortcut.
    return self._id

  @property
  def tag(self):
    """Returns image tag string."""
    return self._image_opts.tag

  def __enter__(self):
    """Makes Image usable with "with" statement."""
    self.Build()
    return self

  # pylint: disable=redefined-builtin
  def __exit__(self, type, value, traceback):
    """Makes Image usable with "with" statement."""
    self.Remove()

  def __del__(self):
    """Makes sure that build artifacts are cleaned up."""
    self.Remove()

  def Build(self):
    """Calls "docker build".

    Raises:
      ImageBuildError: if the image could not be built.
    """
    log.info('Building docker image %s from %s/Dockerfile:',
             self.tag, self._image_opts.dockerfile_dir)

    width, _ = console_attr_os.GetTermSize()
    log.status.Print(DOCKER_OUTPUT_BEGIN.center(width, DOCKER_OUTPUT_LINE_CHAR))

    build_res = self._docker_client.build(
        path=self._image_opts.dockerfile_dir,
        tag=self.tag,
        quiet=False, fileobj=None, nocache=self._image_opts.nocache,
        rm=self._image_opts.rm)

    info = None
    error = None
    error_detail = None
    log_records = []
    try:
      for line in build_res:
        line = line.strip()
        if not line:
          continue
        log_record = json.loads(line)
        log_records.append(log_record)
        if 'stream' in log_record:
          info = log_record['stream'].strip()
          log.status.Print(info)
        if 'error' in log_record:
          error = log_record['error'].strip()
          # will be logged to log.error in the thrown exception
          log.status.Print(error)
        if 'errorDetail' in log_record:
          error_detail = log_record['errorDetail']['message'].strip()
          log.status.Print(error_detail)
    except docker.errors.APIError as e:
      log.error(e.explanation)
      error = e.explanation
      error_detail = ''
    finally:
      log.status.Print(DOCKER_OUTPUT_LINE_CHAR * width + '\n')

    if not log_records:
      raise ImageBuildError(
          'Error building docker image {0} [with no output]'.format(self.tag))

    success_message = log_records[-1].get(_STREAM)
    if success_message:
      m = _SUCCESSFUL_BUILD_PATTERN.match(success_message)
      if m:
        # The build was successful.
        self._id = m.group(1)
        log.info('Image %s built, id = %s', self.tag, self.id)
        return

    raise ImageBuildError('Docker build aborted: ' + error)

  def Remove(self):
    """Calls "docker rmi"."""
    # This will be done automatically by the cleanup.
    self._id = None


def KwargsFromEnv(host, cert_path, tls_verify):
  """Helper to build docker.Client constructor kwargs from the environment."""
  log.debug('Detected docker environment variables: DOCKER_HOST=%s, '
            'DOCKER_CERT_PATH=%s, DOCKER_TLS_VERIFY=%s', host, cert_path,
            tls_verify)
  params = {}

  if host:
    params['base_url'] = (host.replace('tcp://', 'https://') if tls_verify
                          else host)
  elif sys.platform.startswith('linux'):
    # if this is a linux user, the default value of DOCKER_HOST should be the
    # unix socket.

    # first check if the socket is valid to give a better feedback to the user.
    if os.path.exists(DEFAULT_LINUX_DOCKER_HOST):
      sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
      try:
        sock.connect(DEFAULT_LINUX_DOCKER_HOST)
        params['base_url'] = 'unix://' + DEFAULT_LINUX_DOCKER_HOST
      except socket.error:
        log.warning('Found a stale /var/run/docker.sock, '
                    'did you forget to start your Docker daemon?')
      finally:
        sock.close()

  if tls_verify and cert_path:
    # assert_hostname=False is needed for boot2docker to work with our custom
    # registry.
    params['tls'] = docker.tls.TLSConfig(
        client_cert=(os.path.join(cert_path, 'cert.pem'),
                     os.path.join(cert_path, 'key.pem')),
        ca_cert=os.path.join(cert_path, 'ca.pem'),
        verify=True,
        ssl_version=ssl.PROTOCOL_TLSv1,
        assert_hostname=False)
  return params


def NewDockerClientNoCheck(**kwargs):
  """Factory method for building a docker.Client from environment variables.

  Args:
    **kwargs: Any kwargs will be passed to the docker.Client constructor and
      override any determined from the environment.

  Returns:
    A docker.Client instance.

  Raises:
    DockerDaemonConnectionError: If the Docker daemon isn't responding.
  """
  kwargs['version'] = config.DOCKER_PY_VERSION
  kwargs['timeout'] = config.DOCKER_D_REQUEST_TIMEOUT

  if 'base_url' not in kwargs:
    raise DockerDaemonConnectionError(DOCKER_CONNECTION_ERROR)
  return docker.Client(**kwargs)


def NewDockerClient(local=False, **kwargs):
  """Factory method for building a docker.Client from environment variables.

  Args:
    local: bool, whether this is a local docker build
    **kwargs: Any kwargs will be passed to the docker.Client constructor and
      override any determined from the environment.

  Returns:
    A docker.Client instance.

  Raises:
    DockerDaemonConnectionError: If the Docker daemon isn't responding.
  """
  client = NewDockerClientNoCheck(**kwargs)
  try:
    client.ping()
  except requests.exceptions.SSLError as e:
    log.error('Failed to connect to Docker daemon due to an SSL problem: %s', e)
    msg = ''
    # There is a common problem with TLS and docker-py on OS X Python
    # installations, especially the one in Homebrew.
    if platforms.Platform.Current() == platforms.OperatingSystem.MACOSX:
      msg += ('\n\nThis may be due to the issue described at the following '
              'URL, especially if you\'re using a Python installation from '
              'Homebrew: '
              'https://github.com/docker/docker-py/issues/465\n\n'
              'One possible workaround is to set the environment variable '
              'CLOUDSDK_PYTHON to another Python executable (that is, not the '
              'one from Homebrew).')
      try:
        # This is a part of requests[security], which is a set of optional
        # dependencies for the requests library. If installed, it can work
        # around the SSL issue.
        # pylint: disable=g-import-not-at-top
        import ndg  # pylint: disable=import-error,unused-variable
        # pylint: enable=g-import-not-at-top
      except ImportError:
        msg += ('\n\nYou do not appear to have requests[security] installed. '
                'Consider installing this package (which bundles security '
                'libraries that may fix this problem) to the current Python '
                'installation as another possible workaround:\n'
                '  pip install requests[security]\n'
                'If you do this, you must set the environment variable '
                'CLOUDSDK_PYTHON_SITEPACKAGES before running the Cloud SDK '
                'again:\n'
                '  export CLOUDSDK_PYTHON_SITEPACKAGES=1')
    raise DockerDaemonConnectionError(
        'Couldn\'t connect to the Docker daemon due to an SSL problem.' + msg)
  except requests.exceptions.ConnectionError, e:
    log.error('Failed to connect to Docker Daemon due to: %s', e)
    msg = DOCKER_CONNECTION_ERROR
    if local:
      msg += '\n' + DOCKER_CONNECTION_ERROR_LOCAL
    raise DockerDaemonConnectionError(msg)
  return client
