# Copyright 2014 Google Inc. All Rights Reserved.

"""Wrapper around Docker registry to push Docker Images onto GCS.

See BuildAndPushDockerImage for more details.
"""

import os

from googlecloudsdk.appengine.lib.docker import containers
from googlecloudsdk.appengine.lib.images import config
from googlecloudsdk.appengine.lib.images import registry
from googlecloudsdk.appengine.lib.images import util
from googlecloudsdk.appengine.lib.runtimes import nodejs


def _GetDomainAndDisplayId(project_id):
  """Returns tuple (displayed app id, domain)."""
  l = project_id.split(':')
  if len(l) == 1:
    return l[0], None
  return l[1], l[0]


def _GetImageName(display, domain, module, version):
  """Returns image tag according to App Engine convention."""
  return (config.DOCKER_IMAGE_NAME_DOMAIN_FORMAT if domain
          else config.DOCKER_IMAGE_NAME_FORMAT).format(
              display=display, domain=domain, module=module, version=version)


def BuildAndPushDockerImage(appyaml_path, project_id, module,
                            version, runtime, docker_client):
  """Builds Docker image and pushes it onto Google Cloud Storage.

  Workflow:
      Connects to Docker daemon.
      Builds user image.
      Pushes an image to GCR.

  Args:
    appyaml_path: str, Path to the app.yaml for the module.
        Dockerfile must be located in the same directory.
    project_id: str, App Engine application id.
    module: str, Name of the module.
    version: str, Major version of the module.
    runtime: str, Runtime of the module.
    docker_client: docker.Client instance.

  Raises:
    InternalError: errors in util.FindOrCopyDockerfile().
    util.NoDockerfileError: If there is no default Dockerfile for a given
        runtime and user did not provide one (raised by
        util.FindOrCopyDockerfile).
  """
  dockerfile_dir = os.path.dirname(appyaml_path)
  dockerfile = os.path.join(dockerfile_dir, 'Dockerfile')

  # TODO(user): Once it becomes available, use the fingerprinting based
  # functionality we use for node for all runtimes.
  if runtime == 'nodejs':
    configurator = nodejs.Fingerprint(dockerfile_dir, deploy=True)
    if not configurator:
      raise util.NoDockerfileError("This doesn't look like a node.js app.  "
                                   'Add a package.json with a scripts.start '
                                   'section or create your own Dockerfile.')
    configurator.GenerateConfigs()
  elif runtime == 'custom' and not os.path.exists(dockerfile):
    raise util.NoDockerfileError('You must provide your own Dockerfile '
                                 'when using a custom runtime.  Otherwise '
                                 'provide a "runtime" field with one of the '
                                 'supported runtimes.')
  else:
    util.FindOrCopyDockerfile(runtime, dockerfile_dir)

  display, domain = _GetDomainAndDisplayId(project_id)

  with containers.Image(docker_client, containers.ImageOptions(
      dockerfile_dir=dockerfile_dir,
      tag=_GetImageName(display, domain, module, version),
      nocache=False)) as image:

    r = registry.Registry(docker_client)
    r.Push(image)
