# Copyright 2014 Google Inc. All Rights Reserved.

"""Magic constants for images module."""

# The version of the docker API the docker-py client uses.
# Warning: other versions might have different return values for some functions.
DOCKER_PY_VERSION = '1.16'

# Timeout of HTTP request from docker-py client to docker daemon, in seconds.
DOCKER_D_REQUEST_TIMEOUT = 300

DOCKER_IMAGE_NAME_FORMAT = '{display}.{module}.{version}'
DOCKER_IMAGE_NAME_DOMAIN_FORMAT = '{domain}.{display}.{module}.{version}'

# Base Docker images.
DOCKER_BASE_IMAGE_STORAGE_PATH = ''
DOCKER_BASE_IMAGE_NAMESPACE = 'google'
DOCKER_BASE_IMAGE_NAME_FORMAT = '{namespace}/appengine-{runtime}'

# Subdirectory where all docker related stuff goes.
DOCKER_INSTALLATION_DIR = 'docker'

# Name of the a Dockerfile.
DOCKERFILE = 'Dockerfile'

# A map of runtimes values if they need to be overwritten to match our
# base Docker images naming rules.
CANONICAL_RUNTIMES = {
    'java7': 'java',
    'python': 'python27'}

HELPER_IMAGES = ['log-processor', 'log-server']
