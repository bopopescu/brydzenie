# Copyright 2014 Google Inc. All Rights Reserved.

"""Helper Functions for appengine.lib.images module."""

import atexit
import os

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import pkg_resources

import googlecloudsdk.appengine
from googlecloudsdk.appengine.lib.images import config


class NoDefaultDockerfileError(exceptions.Error):
  """No default Dockerfile for a given runtime."""


class NoDockerfileError(exceptions.Error):
  """No Dockerfile found (neither user provided, nor default)."""


def FindOrCopyDockerfile(runtime, dst, cleanup=True):
  """Copies default Dockerfile for a given runtime into destination directory.

  Default Dockerfile for runtime is used if there is no user provided dockerfile
  in the destination directory.

  Args:
    runtime: str, Runtime that we're looking for the Dockerfile for.
    dst: str, Directory path where to check for and copy to the Dockerfile.
    cleanup: bool, If true, delete the file on gcloud exit.

  Raises:
    InternalError: if there is no directory with default Dockerfiles
        (raised by _CopyDefaultDockerfile).
    NoDefaultDockerfileError: if there is no default Dockerfile for a given
        runtime.
  """
  log.info('Looking for the %s in %s', config.DOCKERFILE, dst)
  if os.path.exists(os.path.join(dst, config.DOCKERFILE)):
    log.info('Using %s found in %s', config.DOCKERFILE, dst)
  else:
    try:
      _CopyDefaultDockerfile(runtime, dst, cleanup)
    except NoDefaultDockerfileError as e:
      log.error('%s %s', e, 'Or put your own Dockerfile into the directory '
                'with your module yaml configuration.')
      raise NoDockerfileError()


def GetAllManagedVMsRuntimes():
  """Returns the list of runtimes supported by Managed VMs.

  The list of supported runtimes is built based on the default Dockerfiles
  provided with the SDK.

  Raises:
    InternalError: if there is no directory with default Dockerfiles.

  Returns:
    [str], List of runtimes supported for Managed VMs.
  """
  return _ListSupportedRuntimes(_GetDefaultDockerfilesDir())


def _GetCanonicalRuntime(runtime):
  """Retuns canonical runtime name (might be equal to the given value)."""
  res = config.CANONICAL_RUNTIMES.get(runtime, runtime)
  if res != runtime:
    log.info(
        'Runtime [{runtime}] is substituted by [{canonical_runtime}]'.format(
            runtime=runtime, canonical_runtime=res))
  return res


def _ListSupportedRuntimes(dockerfiles_dir):
  """Lists supported runtimes based on the content of a given directory.

  Args:
    dockerfiles_dir: str, The directory with default Dockerfiles for apps. The
        Dockerfiles are under format is {runtime}_app/Dockerfile.

  Returns:
    [str], list of runtimes found.
  """
  resources = pkg_resources.ListPackageResources(dockerfiles_dir)
  # Strips trailing '_app/'.
  return [x[:-5] for x in resources if not x.startswith('.')]


def _GetDefaultDockerfilesDir():
  """Retuns path containing default Dockerfiles for Managed VMs apps.

  Returns:
    str, The path with default Dockerfiles for Managed VMs runtimes.
  """
  return os.path.join(
      os.path.dirname(googlecloudsdk.appengine.__file__), 'dockerfiles')


def _CopyDefaultDockerfile(runtime, dst, cleanup):
  """Copies default Dockerfile for a given runtime into destination directory.

  Args:
    runtime: str, Runtime that we're looking for the Dockerfile for.
    dst: str, Directory path where to copy the Dockerfile.
    cleanup: bool, If true, delete the file on gcloud exit.

  Raises:
    InternalError: if there is no directory with default Dockerfiles.
    NoDefaultDockerfileError: if there is no default Dockerfile for a given
        runtime.
  """
  log.info('Looking for the default %s for runtime [%s]',
           config.DOCKERFILE, runtime)
  runtime = _GetCanonicalRuntime(runtime)
  default_dockerfiles_dir = _GetDefaultDockerfilesDir()
  src = os.path.join(
      default_dockerfiles_dir,
      '{runtime}_app'.format(runtime=runtime),
      config.DOCKERFILE)
  try:
    src_data = pkg_resources.GetData(src)
  except IOError:
    raise NoDefaultDockerfileError(
        'No default {dockerfile} for runtime [{runtime}] in the SDK. '
        'Use one of the supported runtimes: [{supported}].'.format(
            dockerfile=config.DOCKERFILE, runtime=runtime, supported='|'.join(
                _ListSupportedRuntimes(default_dockerfiles_dir))))

  log.info('%s for runtime [%s] is found in %s. Copying it into application '
           'directory.', config.DOCKERFILE, runtime, default_dockerfiles_dir)

  with open(os.path.join(dst, os.path.basename(src)), 'w') as dst_file:
    dst_file.write(src_data)

  # Delete the file after we're done if necessary.
  if cleanup:
    atexit.register(Clean, os.path.join(dst, config.DOCKERFILE))


def Clean(path):
  try:
    os.remove(path)
  except OSError as e:
    log.debug('Error removing generated %s: %s', path, e)


def FullImageName(runtime):
  return config.DOCKER_BASE_IMAGE_NAME_FORMAT.format(
      namespace=config.DOCKER_BASE_IMAGE_NAMESPACE, runtime=runtime)


def FullVersionedName(image_name, version):
  return '{image}:{version}'.format(
      image=image_name, version=version)
