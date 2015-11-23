# Copyright 2014 Google Inc. All Rights Reserved.

"""Docker registry to push docker images to Google Container Registry.

Registry runs in a Docker container.
"""

import json
import time

from googlecloudsdk.core import log
from googlecloudsdk.core.docker import constants as const_lib


_GOOGLE_NAMESPACE_PREFIX = 'google/'
_RETRIES = 60


class Error(Exception):
  """Base exception for registry module."""


class ImageNotReadyError(Error):
  """Raised when an image we pulled never becomes ready."""


def _Retry(func, *args, **kwargs):
  """Retries the function if an exception occurs.

  Args:
    func: The function to call and retry.
    *args: Args to pass to the function.
    **kwargs: Kwargs to pass to the function.

  Returns:
    Whatever the function returns.
  """
  retries = _RETRIES
  while True:
    try:
      return func(*args, **kwargs)
    except Exception as e:  # pylint: disable=broad-except
      retries -= 1
      if retries > 0:
        log.info('Exception {e} thrown in {func}. Retrying.'.format(
            e=e, func=func.__name__))
        time.sleep(1)
      else:
        raise e


def ProgressHandler(action, func_with_output_lines):
  """Handles the streaming output of the docker client.

  Args:
    action: str, action verb for logging purposes, for example "push" or "pull".
    func_with_output_lines: a function streaming output from the docker client.
  Raises:
    Error: if a problem occured during the operation with an explanation
           string if possible.
  """
  for line in func_with_output_lines():
    line = line.strip()
    if not line:
      continue
    log_record = json.loads(line)
    if 'status' in log_record:
      feedback = log_record['status'].strip()
      if 'progress' in log_record:
        feedback += ': ' + log_record['progress'] + '\r'
      else:
        feedback += '\n'
      log.info(feedback)
    elif 'error' in log_record:
      error = log_record['error'].strip()
      log.error(error)
      raise Error('Unable to %s the image to/from the registry: "%s"' %
                  (action, error))
    elif 'errorDetail' in log_record:
      error_detail = log_record['errorDetail'] or 'Unknown Error'
      raise Error('Unable to push the image to the registry: "%s"'
                  % error_detail)


class Registry(object):
  """Docker Registry."""

  def __init__(self, docker_client):
    """Initializer for Registry. Uses the Google Container Registry.

    Args:
      docker_client: docker.Client instance.
    """
    self.addr = const_lib.APPENGINE_REGISTRY
    self._docker_client = docker_client
    log.debug('Configured access to {server}.'.format(server=self.addr))

  def GetRepoImageTag(self, image_tag):
    return '%s/gcloud/%s' % (self.addr, image_tag)

  def Push(self, image):
    """Calls "docker push" command.

    Args:
      image: containers.Image, An image to push onto GCR.
    """
    repo_image_tag = self.GetRepoImageTag(image.tag)
    self._docker_client.tag(image.id, repo_image_tag, force=True)

    log.info('Pushing image to Google Container Registry...\n')

    def InnerPush():
      return self._docker_client.push(repo_image_tag,
                                      stream=True)

    _Retry(ProgressHandler, 'push', InnerPush)

  def _WaitForImageReady(self, image_name):
    """Waits until image with image_name can be found."""

    for _ in range(_RETRIES):
      images = self._docker_client.images(
          name=image_name, quiet=True, all=False, viz=False)
      if images:
        break
      time.sleep(1)
    else:
      raise ImageNotReadyError('Image: %s never became ready.' % image_name)
