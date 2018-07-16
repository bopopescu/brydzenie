# Copyright 2015 Google Inc. All Rights Reserved.

"""Fingerprinting code for the node.js runtime."""

import atexit
import json
import os
import textwrap

from googlecloudsdk.core import log

from googlecloudsdk.appengine.lib import fingerprinting
from googlecloudsdk.appengine.lib.images import config
from googlecloudsdk.appengine.lib.images import util

NODEJS_RUNTIME_NAME = 'nodejs'

# TODO(user): move these into the node_app directory.
NODEJS_APP_YAML = textwrap.dedent("""\
    vm: true
    api_version: 1
    """)
DOCKERIGNORE = textwrap.dedent("""\
    node_modules
    .dockerignore
    Dockerfile
    .git
    .hg
    .svn
    """)


class NodeJSConfigurator(fingerprinting.Configurator):
  """Generates configuration for a node.js class."""

  def __init__(self, path, got_package_json, got_npm_start,
               got_shrinkwrap,
               deploy):
    """Constructor.

    Args:
      path: (str) Root path of the source tree.
      got_package_json: (bool) If true, the runtime contains a package.json
        file and we should do an npm install while building the docker image.
      got_npm_start: (bool) If true, the runtime contains a "start" script in
        the package.json and we should do "npm start" to start the package.
        If false, we assume there is a server.js file and we do "node
        server.js" instead.
      got_shrinkwrap: (bool) True if the user provided an
        "npm-shrinkwrap.json" file.
      deploy: (bool) True if this is being driven from the "deploy" command. In
        this case, we want to not generate app.yaml and make the code cleanup
        whatever we generate.
    """

    self.root = path
    self.got_package_json = got_package_json
    self.got_npm_start = got_npm_start
    self.got_shrinkwrap = got_shrinkwrap
    self.deploy = deploy

  def GenerateConfigs(self):
    """Generate all config files for the module."""
    # Write "Saving file" messages to the user or to log depending on whether
    # we're in "deploy."
    if self.deploy:
      notify = log.info
    else:
      notify = log.status.Print

    files_created = False
    dockerfile = os.path.join(self.root, config.DOCKERFILE)
    if not os.path.exists(dockerfile):
      notify('Saving [%s] to [%s].' % (config.DOCKERFILE, self.root))
      util.FindOrCopyDockerfile(NODEJS_RUNTIME_NAME, self.root,
                                cleanup=self.deploy)

      # Customize the dockerfile.
      os.chmod(dockerfile, os.stat(dockerfile).st_mode | 0200)
      with open(dockerfile, 'a') as out:

        # Generate copy for shrinkwrap file.
        if self.got_shrinkwrap:
          out.write('COPY npm-shrinkwrap.json /app/\n')

        # Generate npm install if there is a package.json.
        if self.got_package_json:
          out.write('COPY package.json /app/\n'
                    'RUN npm install\n')

        out.write('COPY . /app/\n')

        # Generate the appropriate start command.
        if self.got_npm_start:
          out.write('CMD npm start\n')
        else:
          out.write('CMD node server.js\n')

      files_created = True

    # Generate app.yaml.
    if not self.deploy:
      app_yaml = os.path.join(self.root, 'app.yaml')
      if not os.path.exists(app_yaml):
        notify('Saving [app.yaml] to [%s].' % self.root)
        with open(app_yaml, 'w') as f:
          f.write(NODEJS_APP_YAML)
        files_created = True

    # Generate .dockerignore TODO(user): eventually this file will just be
    # copied verbatim.
    dockerignore = os.path.join(self.root, '.dockerignore')
    if not os.path.exists(dockerignore):
      notify('Saving [.dockerignore] to [%s].' % self.root)
      with open(dockerignore, 'w') as f:
        f.write(DOCKERIGNORE)
      files_created = True

      if self.deploy:
        atexit.register(util.Clean, dockerignore)

    if not files_created:
      notify('All config files already exist, not generating anything.')


def Fingerprint(path, deploy=False):
  """Check for a Node.js app.

  Args:
    path: (str) Application path.
    deploy: (bool) Set to true if called from the "deploy" path.

  Returns:
    (NodeJSConfigurator or None) Returns a module if the path contains a
    node.js app.
  """
  log.info('Checking for Node.js.')
  package_json = os.path.join(path, 'package.json')
  got_shrinkwrap = False

  if not os.path.isfile(package_json):
    log.debug('node.js checker: No package.json file.')
    got_package_json = False
    got_npm_start = False
  else:
    got_package_json = True

    # Try to read the package.json file.
    try:
      with open(package_json) as f:
        contents = json.load(f)
    except (IOError, ValueError) as ex:
      # If we have an invalid or unreadable package.json file, there's
      # something funny going on here so fail recognition.
      log.debug('node.js checker: error accesssing package.json: %r' % ex)
      return None

    # See if we've got a scripts.start field.
    got_npm_start = bool(contents.get('scripts', {}).get('start'))

    # See if we've got a shrinkwrap file.
    if os.path.isfile(os.path.join(path, 'npm-shrinkwrap.json')):
      got_shrinkwrap = True

  if got_npm_start or os.path.exists(os.path.join(path, 'server.js')):
    return NodeJSConfigurator(path, got_package_json, got_npm_start,
                              got_shrinkwrap, deploy)
  else:
    log.debug('nodejs. checker: No npm start and no server.js')
    return None
