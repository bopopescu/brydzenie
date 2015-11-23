# Copyright 2015 Google Inc. All Rights Reserved.
"""Command for deleting managed instance group."""
from googlecloudsdk.compute.lib import autoscaler_util
from googlecloudsdk.compute.lib import base_classes


class Delete(base_classes.ZonalDeleter):
  """Delete Google Compute Engine managed instance group."""

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def _DeleteAutoscalersRequests(self, args):
    mig_refs = self.reference_creator(args.names, args)
    zone = mig_refs[0].zone
    autoscalers_to_delete = autoscaler_util.AutoscalersForMigs(
        mig_names=[mig_ref.Name() for mig_ref in mig_refs],
        autoscalers=autoscaler_util.AutoscalersForZone(
            zone=zone,
            project=self.project,
            compute=self.compute,
            http=self.http,
            batch_url=self.batch_url),
        project=self.project,
        zone=zone,
    )

    requests = []
    for autoscaler in autoscalers_to_delete:
      as_ref = self.CreateZonalReference(autoscaler.name, zone)
      request = self.messages.ComputeAutoscalersDeleteRequest(
          project=self.project)
      request.zone = zone
      request.autoscaler = as_ref.Name()
      requests.append(request)
    return requests

  def Run(self, args):
    # CreateRequests() propmpts user to confirm deletion so it should be a first
    # thing to be executed in this function.
    delete_managed_instance_groups_requests = self.CreateRequests(args)
    super(Delete, self).Run(
        args, request_protobufs=self._DeleteAutoscalersRequests(args),
        service=self.compute.autoscalers)
    super(Delete, self).Run(
        args, request_protobufs=delete_managed_instance_groups_requests)


Delete.detailed_help = {
    'brief': 'Delete Google Compute Engine managed instance groups',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine managed instance
groups.
        """,
}
