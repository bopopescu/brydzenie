# Copyright 2015 Google Inc. All Rights Reserved.

"""Upgrade cluster command."""
import argparse

from googlecloudsdk.core import log

from apitools.base import py as apitools_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.container.lib import api_adapter
from googlecloudsdk.container.lib import util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Upgrade(base.Command):
  """Upgrade the Kubernetes version of an existing container cluster."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        'name',
        metavar='NAME',
        help='The name of the cluster to upgrade.')
    parser.add_argument(
        '--cluster-version',
        help='The kubernetes release version to change the cluster to.'
        ' Omit to upgrade to the latest version offered by the server.')
    parser.add_argument(
        '--main',
        help=argparse.SUPPRESS,
        action='store_true')
    parser.add_argument(
        '--no-wait',
        dest='wait',
        action='store_false',
        help='Return after issuing upgrade request without polling the'
        ' operation for completion.')

  # TODO(user): The preference now is to throw util.Error directly (see
  # comment in cl/93364826). Change this throughout sdk/container/...
  @exceptions.RaiseToolExceptionInsteadOf(util.Error)
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    adapter = self.context['api_adapter']

    cluster_ref = adapter.ParseCluster(args.name)

    # Make sure it exists (will raise appropriate error if not)
    adapter.GetCluster(cluster_ref)

    options = api_adapter.UpdateClusterOptions(
        version=args.cluster_version,
        update_main=args.main,
        update_nodes=(not args.main))

    try:
      op_ref = adapter.UpdateCluster(cluster_ref, options)
    except apitools_base.HttpError as error:
      raise exceptions.HttpException(util.GetError(error))

    if args.wait:
      adapter.WaitForOperation(
          op_ref, 'Upgrading {0}'.format(cluster_ref.clusterId))

      log.UpdatedResource(cluster_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpgradeBeta(Upgrade):
  """Upgrade an existing cluster for running containers."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpgradeAlpha(Upgrade):
  """Upgrade an existing cluster for running containers."""
