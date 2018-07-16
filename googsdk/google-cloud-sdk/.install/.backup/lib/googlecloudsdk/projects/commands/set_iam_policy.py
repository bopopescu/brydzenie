# Copyright 2015 Google Inc. All Rights Reserved.

"""Command to set IAM policy for a resource."""

from protorpc.messages import DecodeError

from apitools.base.py import encoding
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.projects.lib import util


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetIamPolicy(base.Command):
  """Set IAM policy for a Project.

  This command sets the IAM policy for a Project, given a Project ID and a
  file that contains the JSON encoded IAM policy.
  """

  detailed_help = {
      'brief': 'Set IAM policy for a Project.',
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          The following command will read an IAM policy defined in a JSON file
          'policy.json' and set it for a Project with identifier
          'example-project-id-1'

            $ {command} example-project-id-1 policy.json
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('id', help='Project ID')
    parser.add_argument('policy_file', help='JSON file with the IAM policy')

  @util.HandleHttpError
  def Run(self, args):
    projects = self.context['projects_client']
    messages = self.context['projects_messages']
    resources = self.context['projects_resources']

    project_ref = resources.Parse(args.id,
                                  collection='cloudresourcemanager.projects')

    try:
      with open(args.policy_file) as policy_file:
        policy_json = policy_file.read()
    except EnvironmentError:
      # EnvironmnetError is parent of IOError, OSError and WindowsError.
      # Raised when file does not exist or can't be opened/read.
      raise exceptions.BadFileException(
          'Unable to read policy file {0}'.format(args.policy_file))

    try:
      policy = encoding.JsonToMessage(messages.Policy, policy_json)
    except (ValueError, DecodeError):
      # ValueError is raised when JSON is badly formatted
      # DecodeError is raised when etag is badly formatted (not proper Base64)
      raise exceptions.BadFileException(
          'Policy file {0} is not a properly formatted JSON policy file'.format(
              args.policy_file))

    policy_request = messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
        resource=project_ref.Name(),
        setIamPolicyRequest=messages.SetIamPolicyRequest(policy=policy))
    return projects.projects.SetIamPolicy(policy_request)

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    # pylint:disable=not-callable, self.format is callable.
    self.format(result)
