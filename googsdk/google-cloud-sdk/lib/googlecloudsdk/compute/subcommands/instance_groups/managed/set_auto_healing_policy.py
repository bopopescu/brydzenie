# Copyright 2015 Google Inc. All Rights Reserved.
"""Command for setting auto-healing policy of managed instance group."""
from googlecloudsdk.calliope import base
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetAutoHealingPolicy(base_classes.BaseAsyncMutator):
  """Set auto-healing policy of instance group manager."""

  @staticmethod
  def Args(parser):
    parser.add_argument('name', help='Managed instance group name.')
    parser.add_argument(
        '--http-health-check',
        help=('Specifies the HTTP health check object used for auto-healing '
              'instances in this group.'))
    utils.AddZoneFlag(
        parser,
        resource_type='instance group manager',
        operation_type='set auto-healing policy')

  @property
  def method(self):
    return 'SetAutoHealingPolicy'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateRequests(self, args):
    ref = self.CreateZonalReference(args.name, args.zone)
    auto_healing_policies = []
    if args.http_health_check:
      health_check_ref = self.CreateGlobalReference(
          args.http_health_check,
          resource_type='httpHealthChecks')
      auto_healing_policies.append(
          self.messages.InstanceGroupManagerAutoHealingPolicy(
              healthCheck=health_check_ref.SelfLink()))
    request = (
        self.messages.ComputeInstanceGroupManagersSetAutoHealingPolicyRequest(
            project=self.project,
            zone=ref.zone,
            instanceGroupManager=ref.Name(),
            instanceGroupManagersSetAutoHealingPolicyRequest=(
                self.messages.InstanceGroupManagersSetAutoHealingPolicyRequest(
                    autoHealingPolicies=auto_healing_policies)))
    )
    return [request]


SetAutoHealingPolicy.detailed_help = {
    'brief': 'Set auto-healing policy for managed instance group.',
    'DESCRIPTION': """
        *{command}* updates the auto-healing policy for an existing managed
instance group.

If --http-health-check is specified, the resulting auto-healing policy will be
triggered by the health-check i.e. the auto-healing action (RECREATE) on an
instance will be performed if the health-check signals that the instance is
UNHEALTHY. If --http-health-check is not specified, the resulting auto-healing
policy will be triggered by instance's status i.e. the auto-healing action
(RECREATE) on an instance will be performed if the instance.status is not
RUNNING.
""",
}
