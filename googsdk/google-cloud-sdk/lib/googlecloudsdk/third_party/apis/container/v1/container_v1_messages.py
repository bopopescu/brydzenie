"""Generated message classes for container version v1.

The Google Container Engine API is used for building and managing container-
based applications, powered by the open source Kubernetes technology.
"""
# NOTE: This file is autogenerated and should not be edited by hand.

from protorpc import messages as _messages

from apitools.base.py import encoding


package = 'container'


class Cluster(_messages.Message):
  """A Google Container Engine cluster.

  Enums:
    StatusValueValuesEnum: [Output only] The current status of this cluster.

  Fields:
    clusterIpv4Cidr: The IP address range of the container pods in this
      cluster, in [CIDR](http://en.wikipedia.org/wiki/Classless_Inter-
      Domain_Routing) notation (e.g. `10.96.0.0/14`). Leave blank to have one
      automatically chosen or specify a `/14` block in `10.0.0.0/8`.
    createTime: [Output only] The time the cluster was created, in
      [RFC3339](https://www.ietf.org/rfc/rfc3339.txt) text format.
    currentMainVersion: [Output only] The current software version of the
      main endpoint.
    currentNodeVersion: [Output only] The current version of the node software
      components. If they are currently at different versions because they're
      in the process of being upgraded, this reflects the minimum version of
      any of them.
    description: An optional description of this cluster.
    endpoint: [Output only] The IP address of this cluster's main endpoint.
      The endpoint can be accessed from the internet at
      `https://username:password@endpoint/`.  See the `mainAuth` property of
      this resource for username and password information.
    initialClusterVersion: [Output only] The software version of the main
      and kubelets used in the cluster when it was first created. The version
      can be upgraded over time.
    initialNodeCount: The number of nodes to create in this cluster. You must
      ensure that your Compute Engine <a href="/compute/docs/resource-
      quotas">resource quota</a> is sufficient for this number of instances.
      You must also have available firewall and routes quota.
    instanceGroupUrls: [Output only] The resource URLs of [instance
      groups](/compute/docs/instance-groups/) associated with this cluster.
    loggingService: The logging service that the cluster should write logs to.
      Currently available options:  * `logging.googleapis.com` - the Google
      Cloud Logging service. * `none` - no logs will be exported from the
      cluster. * "" - default value: the default is `logging.googleapis.com`.
    mainAuth: The authentication information for accessing the main.
    monitoringService: The monitoring service that the cluster should write
      metrics to. Currently available options:  * `monitoring.googleapis.com`
      - the Google Cloud Monitoring service. * `none` - no metrics will be
      exported from the cluster. * "" - default value: the default is
      `monitoring.googleapis.com`.
    name: The name of this cluster. The name must be unique within this
      project and zone, and can be up to 40 characters with the following
      restrictions:  * Lowercase letters, numbers, and hyphens only. * Must
      start with a letter. * Must end with a number or a letter.
    network: The name of the Google Compute Engine
      [network](/compute/docs/networking#networks_1) to which the cluster is
      connected. If left unspecified, the `default` network will be used.
    nodeConfig: Parameters used in creating the cluster's nodes. See the
      descriptions of the child properties of `nodeConfig`.  If unspecified,
      the defaults for all child properties are used.
    nodeIpv4CidrSize: [Output only] The size of the address space on each node
      for hosting containers. This is provisioned from within the
      `container_ipv4_cidr` range.
    selfLink: [Output only] Server-defined URL for the resource.
    servicesIpv4Cidr: [Output only] The IP address range of the Kubernetes
      services in this cluster, in [CIDR](http://en.wikipedia.org/wiki
      /Classless_Inter-Domain_Routing) notation (e.g. `1.2.3.4/29`). Service
      addresses are typically put in the last `/16` from the container CIDR.
    status: [Output only] The current status of this cluster.
    statusMessage: [Output only] Additional information about the current
      status of this cluster, if available.
    zone: [Output only] The name of the Google Compute Engine
      [zone](/compute/docs/zones#available) in which the cluster resides.
  """

  class StatusValueValuesEnum(_messages.Enum):
    """[Output only] The current status of this cluster.

    Values:
      STATUS_UNSPECIFIED: Not set.
      PROVISIONING: The PROVISIONING state indicates the cluster is being
        created.
      RUNNING: The RUNNING state indicates the cluster has been created and is
        fully usable.
      RECONCILING: The RECONCILING state indicates that some work is actively
        being done on the cluster, such as upgrading the main or node
        software. Details can be found in the `statusMessage` field.
      STOPPING: The STOPPING state indicates the cluster is being deleted.
      ERROR: The ERROR state indicates the cluster may be unusable. Details
        can be found in the `statusMessage` field.
    """
    STATUS_UNSPECIFIED = 0
    PROVISIONING = 1
    RUNNING = 2
    RECONCILING = 3
    STOPPING = 4
    ERROR = 5

  clusterIpv4Cidr = _messages.StringField(1)
  createTime = _messages.StringField(2)
  currentMainVersion = _messages.StringField(3)
  currentNodeVersion = _messages.StringField(4)
  description = _messages.StringField(5)
  endpoint = _messages.StringField(6)
  initialClusterVersion = _messages.StringField(7)
  initialNodeCount = _messages.IntegerField(8, variant=_messages.Variant.INT32)
  instanceGroupUrls = _messages.StringField(9, repeated=True)
  loggingService = _messages.StringField(10)
  mainAuth = _messages.MessageField('MainAuth', 11)
  monitoringService = _messages.StringField(12)
  name = _messages.StringField(13)
  network = _messages.StringField(14)
  nodeConfig = _messages.MessageField('NodeConfig', 15)
  nodeIpv4CidrSize = _messages.IntegerField(16, variant=_messages.Variant.INT32)
  selfLink = _messages.StringField(17)
  servicesIpv4Cidr = _messages.StringField(18)
  status = _messages.EnumField('StatusValueValuesEnum', 19)
  statusMessage = _messages.StringField(20)
  zone = _messages.StringField(21)


class ClusterUpdate(_messages.Message):
  """ClusterUpdate describes an update to the cluster. Exactly one update can
  be applied to a cluster with each request, so at most one field can be
  provided.

  Fields:
    desiredMainVersion: The Kubernetes version to change the main to
      (typically an upgrade). Use "-" to upgrade to the latest version
      supported by the server.
    desiredMonitoringService: The monitoring service that the cluster should
      write metrics to. Currently available options:  *
      "monitoring.googleapis.com" - the Google Cloud Monitoring service *
      "none" - no metrics will be exported from the cluster
    desiredNodeVersion: The Kubernetes version to change the nodes to
      (typically an upgrade). Use `-` to upgrade to the latest version
      supported by the server.
  """

  desiredMainVersion = _messages.StringField(1)
  desiredMonitoringService = _messages.StringField(2)
  desiredNodeVersion = _messages.StringField(3)


class ContainerMainProjectsZonesSignedUrlsCreateRequest(_messages.Message):
  """A ContainerMainProjectsZonesSignedUrlsCreateRequest object.

  Fields:
    createSignedUrlsRequest: A CreateSignedUrlsRequest resource to be passed
      as the request body.
    mainProjectId: The hosted main project in which this main resides.
      This can be either a [project ID or project
      number](https://developers.google.com/console/help/new/#projectnumber).
    zone: The zone of this main's cluster.
  """

  createSignedUrlsRequest = _messages.MessageField('CreateSignedUrlsRequest', 1)
  mainProjectId = _messages.StringField(2, required=True)
  zone = _messages.StringField(3, required=True)


class ContainerMainProjectsZonesTokensCreateRequest(_messages.Message):
  """A ContainerMainProjectsZonesTokensCreateRequest object.

  Fields:
    createTokenRequest: A CreateTokenRequest resource to be passed as the
      request body.
    mainProjectId: The hosted main project in which this main resides.
      This can be either a [project ID or project
      number](https://developers.google.com/console/help/new/#projectnumber).
    zone: The zone of this main's cluster.
  """

  createTokenRequest = _messages.MessageField('CreateTokenRequest', 1)
  mainProjectId = _messages.StringField(2, required=True)
  zone = _messages.StringField(3, required=True)


class ContainerProjectsZonesClustersCreateRequest(_messages.Message):
  """A ContainerProjectsZonesClustersCreateRequest object.

  Fields:
    createClusterRequest: A CreateClusterRequest resource to be passed as the
      request body.
    projectId: The Google Developers Console [project ID or project
      number](https://developers.google.com/console/help/new/#projectnumber).
    zone: The name of the Google Compute Engine
      [zone](/compute/docs/zones#available) in which the cluster resides.
  """

  createClusterRequest = _messages.MessageField('CreateClusterRequest', 1)
  projectId = _messages.StringField(2, required=True)
  zone = _messages.StringField(3, required=True)


class ContainerProjectsZonesClustersDeleteRequest(_messages.Message):
  """A ContainerProjectsZonesClustersDeleteRequest object.

  Fields:
    clusterId: The name of the cluster to delete.
    projectId: The Google Developers Console [project ID or project
      number](https://developers.google.com/console/help/new/#projectnumber).
    zone: The name of the Google Compute Engine
      [zone](/compute/docs/zones#available) in which the cluster resides.
  """

  clusterId = _messages.StringField(1, required=True)
  projectId = _messages.StringField(2, required=True)
  zone = _messages.StringField(3, required=True)


class ContainerProjectsZonesClustersGetRequest(_messages.Message):
  """A ContainerProjectsZonesClustersGetRequest object.

  Fields:
    clusterId: The name of the cluster to retrieve.
    projectId: The Google Developers Console [project ID or project
      number](https://developers.google.com/console/help/new/#projectnumber).
    zone: The name of the Google Compute Engine
      [zone](/compute/docs/zones#available) in which the cluster resides.
  """

  clusterId = _messages.StringField(1, required=True)
  projectId = _messages.StringField(2, required=True)
  zone = _messages.StringField(3, required=True)


class ContainerProjectsZonesClustersListRequest(_messages.Message):
  """A ContainerProjectsZonesClustersListRequest object.

  Fields:
    projectId: The Google Developers Console [project ID or project
      number](https://developers.google.com/console/help/new/#projectnumber).
    zone: The name of the Google Compute Engine
      [zone](/compute/docs/zones#available) in which the cluster resides, or
      "-" for all zones.
  """

  projectId = _messages.StringField(1, required=True)
  zone = _messages.StringField(2, required=True)


class ContainerProjectsZonesClustersUpdateRequest(_messages.Message):
  """A ContainerProjectsZonesClustersUpdateRequest object.

  Fields:
    clusterId: The name of the cluster to upgrade.
    projectId: The Google Developers Console [project ID or project
      number](https://developers.google.com/console/help/new/#projectnumber).
    updateClusterRequest: A UpdateClusterRequest resource to be passed as the
      request body.
    zone: The name of the Google Compute Engine
      [zone](/compute/docs/zones#available) in which the cluster resides.
  """

  clusterId = _messages.StringField(1, required=True)
  projectId = _messages.StringField(2, required=True)
  updateClusterRequest = _messages.MessageField('UpdateClusterRequest', 3)
  zone = _messages.StringField(4, required=True)


class ContainerProjectsZonesGetServerconfigRequest(_messages.Message):
  """A ContainerProjectsZonesGetServerconfigRequest object.

  Fields:
    projectId: The Google Developers Console [project ID or project
      number](https://developers.google.com/console/help/new/#projectnumber).
    zone: The name of the Google Compute Engine
      [zone](/compute/docs/zones#available) to return operations for, or `-`
      for all zones.
  """

  projectId = _messages.StringField(1, required=True)
  zone = _messages.StringField(2, required=True)


class ContainerProjectsZonesOperationsGetRequest(_messages.Message):
  """A ContainerProjectsZonesOperationsGetRequest object.

  Fields:
    operationId: The server-assigned `name` of the operation.
    projectId: The Google Developers Console [project ID or project
      number](https://developers.google.com/console/help/new/#projectnumber).
    zone: The name of the Google Compute Engine
      [zone](/compute/docs/zones#available) in which the cluster resides.
  """

  operationId = _messages.StringField(1, required=True)
  projectId = _messages.StringField(2, required=True)
  zone = _messages.StringField(3, required=True)


class ContainerProjectsZonesOperationsListRequest(_messages.Message):
  """A ContainerProjectsZonesOperationsListRequest object.

  Fields:
    projectId: The Google Developers Console [project ID or project
      number](https://developers.google.com/console/help/new/#projectnumber).
    zone: The name of the Google Compute Engine
      [zone](/compute/docs/zones#available) to return operations for, or `-`
      for all zones.
  """

  projectId = _messages.StringField(1, required=True)
  zone = _messages.StringField(2, required=True)


class CreateClusterRequest(_messages.Message):
  """CreateClusterRequest creates a cluster.

  Fields:
    cluster: A [cluster resource](/container-
      engine/reference/rest/v1/projects.zones.clusters)
  """

  cluster = _messages.MessageField('Cluster', 1)


class CreateSignedUrlsRequest(_messages.Message):
  """A request for signed URLs that allow for writing a file to a private GCS
  bucket for storing backups of hosted main data.

  Fields:
    clusterId: The name of this main's cluster.
    filenames: The names of the files for which a signed URLs are being
      requested.
    projectNumber: The project number for which the signed URLs are being
      requested.  This is the project in which this main's cluster resides.
      Note that this must be a project number, not a project ID.
  """

  clusterId = _messages.StringField(1)
  filenames = _messages.StringField(2, repeated=True)
  projectNumber = _messages.IntegerField(3)


class CreateTokenRequest(_messages.Message):
  """A request for a compute-read-write
  (https://www.googleapis.com/auth/compute) scoped OAuth2 access token for
  <project_number>, to allow hosted mains to make modifications to a user's
  project.

  Fields:
    clusterId: The name of this main's cluster.
    projectNumber: The project number for which the access is being requested.
      This is the project in which this main's cluster resides.  Note that
      this must be a project number, not a project ID.
  """

  clusterId = _messages.StringField(1)
  projectNumber = _messages.IntegerField(2)


class ListClustersResponse(_messages.Message):
  """ListClustersResponse is the result of ListClustersRequest.

  Fields:
    clusters: A list of clusters in the project in the specified zone, or
      across all ones.
  """

  clusters = _messages.MessageField('Cluster', 1, repeated=True)


class ListOperationsResponse(_messages.Message):
  """ListOperationsResponse is the result of ListOperationsRequest.

  Fields:
    operations: A list of operations in the project in the specified zone.
  """

  operations = _messages.MessageField('Operation', 1, repeated=True)


class MainAuth(_messages.Message):
  """The authentication information for accessing the main endpoint.
  Authentication can be done using HTTP basic auth or using client
  certificates.

  Fields:
    clientCertificate: [Output only] Base64-encoded public certificate used by
      clients to authenticate to the cluster endpoint.
    clientKey: [Output only] Base64-encoded private key used by clients to
      authenticate to the cluster endpoint.
    clusterCaCertificate: [Output only] Base64-encoded public certificate that
      is the root of trust for the cluster.
    password: The password to use for HTTP basic authentication when accessing
      the Kubernetes main endpoint. Because the main endpoint is open to
      the internet, you should create a strong password.
    username: The username to use for HTTP basic authentication when accessing
      the Kubernetes main endpoint.
  """

  clientCertificate = _messages.StringField(1)
  clientKey = _messages.StringField(2)
  clusterCaCertificate = _messages.StringField(3)
  password = _messages.StringField(4)
  username = _messages.StringField(5)


class NodeConfig(_messages.Message):
  """Per-node parameters.

  Fields:
    diskSizeGb: Size of the disk attached to each node, specified in GB. The
      smallest allowed disk size is 10GB.  If unspecified, the default disk
      size is 100GB.
    machineType: The name of a Google Compute Engine [machine
      type](/compute/docs/machine-types) (e.g. `n1-standard-1`).  If
      unspecified, the default machine type is `n1-standard-1`.
    oauthScopes: The set of Google API scopes to be made available on all of
      the node VMs under the "default" service account.  The following scopes
      are recommended, but not required, and by default are not included:  *
      `https://www.googleapis.com/auth/compute` is required for mounting
      persistent storage on your nodes. *
      `https://www.googleapis.com/auth/devstorage.read_only` is required for
      communicating with **gcr.io** (the [Google Container Registry
      ](/container-registry/).  If unspecified, no scopes are added.
  """

  diskSizeGb = _messages.IntegerField(1, variant=_messages.Variant.INT32)
  machineType = _messages.StringField(2)
  oauthScopes = _messages.StringField(3, repeated=True)


class Operation(_messages.Message):
  """Defines the operation resource. All fields are output only.

  Enums:
    OperationTypeValueValuesEnum: The operation type.
    StatusValueValuesEnum: The current status of the operation.

  Fields:
    name: The server-assigned ID for the operation.
    operationType: The operation type.
    selfLink: Server-defined URL for the resource.
    status: The current status of the operation.
    statusMessage: If an error has occurred, a textual description of the
      error.
    targetLink: Server-defined URL for the target of the operation.
    zone: The name of the Google Compute Engine
      [zone](/compute/docs/zones#available) in which the operation is taking
      place.
  """

  class OperationTypeValueValuesEnum(_messages.Enum):
    """The operation type.

    Values:
      TYPE_UNSPECIFIED: Not set.
      CREATE_CLUSTER: Cluster create.
      DELETE_CLUSTER: Cluster delete.
      UPGRADE_MASTER: A main upgrade.
      UPGRADE_NODES: A node upgrade.
      REPAIR_CLUSTER: Cluster repair.
      UPDATE_CLUSTER: Cluster update.
    """
    TYPE_UNSPECIFIED = 0
    CREATE_CLUSTER = 1
    DELETE_CLUSTER = 2
    UPGRADE_MASTER = 3
    UPGRADE_NODES = 4
    REPAIR_CLUSTER = 5
    UPDATE_CLUSTER = 6

  class StatusValueValuesEnum(_messages.Enum):
    """The current status of the operation.

    Values:
      STATUS_UNSPECIFIED: Not set.
      PENDING: The operation has been created.
      RUNNING: The operation is currently running.
      DONE: The operation is done, either cancelled or completed.
    """
    STATUS_UNSPECIFIED = 0
    PENDING = 1
    RUNNING = 2
    DONE = 3

  name = _messages.StringField(1)
  operationType = _messages.EnumField('OperationTypeValueValuesEnum', 2)
  selfLink = _messages.StringField(3)
  status = _messages.EnumField('StatusValueValuesEnum', 4)
  statusMessage = _messages.StringField(5)
  targetLink = _messages.StringField(6)
  zone = _messages.StringField(7)


class ServerConfig(_messages.Message):
  """Container Engine Server configuration.

  Fields:
    buildClientInfo: apiserver build BuildData::ClientInfo()
    defaultClusterVersion: What version this server deploys by default.
    validNodeVersions: List of valid node upgrade target versions.
  """

  buildClientInfo = _messages.StringField(1)
  defaultClusterVersion = _messages.StringField(2)
  validNodeVersions = _messages.StringField(3, repeated=True)


class SignedUrls(_messages.Message):
  """Signed URLs that allow for writing a file to a private GCS bucket for
  storing backups of hosted main data.

  Fields:
    signedUrls: The signed URLs for writing the request files, in the same
      order as the filenames in the request.
  """

  signedUrls = _messages.StringField(1, repeated=True)


class StandardQueryParameters(_messages.Message):
  """Query parameters accepted by all methods.

  Enums:
    FXgafvValueValuesEnum: V1 error format.
    AltValueValuesEnum: Data format for response.

  Fields:
    f__xgafv: V1 error format.
    access_token: OAuth access token.
    alt: Data format for response.
    bearer_token: OAuth bearer token.
    callback: JSONP
    fields: Selector specifying which fields to include in a partial response.
    key: API key. Your API key identifies your project and provides you with
      API access, quota, and reports. Required unless you provide an OAuth 2.0
      token.
    oauth_token: OAuth 2.0 token for the current user.
    pp: Pretty-print response.
    prettyPrint: Returns response with indentations and line breaks.
    quotaUser: Available to use for quota purposes for server-side
      applications. Can be any arbitrary string assigned to a user, but should
      not exceed 40 characters.
    trace: A tracing token of the form "token:<tokenid>" or "email:<ldap>" to
      include in api requests.
    uploadType: Legacy upload protocol for media (e.g. "media", "multipart").
    upload_protocol: Upload protocol for media (e.g. "raw", "multipart").
  """

  class AltValueValuesEnum(_messages.Enum):
    """Data format for response.

    Values:
      json: Responses with Content-Type of application/json
      media: Media download with context-dependent Content-Type
      proto: Responses with Content-Type of application/x-protobuf
    """
    json = 0
    media = 1
    proto = 2

  class FXgafvValueValuesEnum(_messages.Enum):
    """V1 error format.

    Values:
      _1: v1 error format
      _2: v2 error format
    """
    _1 = 0
    _2 = 1

  f__xgafv = _messages.EnumField('FXgafvValueValuesEnum', 1)
  access_token = _messages.StringField(2)
  alt = _messages.EnumField('AltValueValuesEnum', 3, default=u'json')
  bearer_token = _messages.StringField(4)
  callback = _messages.StringField(5)
  fields = _messages.StringField(6)
  key = _messages.StringField(7)
  oauth_token = _messages.StringField(8)
  pp = _messages.BooleanField(9, default=True)
  prettyPrint = _messages.BooleanField(10, default=True)
  quotaUser = _messages.StringField(11)
  trace = _messages.StringField(12)
  uploadType = _messages.StringField(13)
  upload_protocol = _messages.StringField(14)


class Token(_messages.Message):
  """A compute-read-write (https://www.googleapis.com/auth/compute) scoped
  OAuth2 access token, to allow hosted mains to make modifications to a
  user's project.

  Fields:
    accessToken: The OAuth2 access token
    expireTime: The expiration time of the token.
  """

  accessToken = _messages.StringField(1)
  expireTime = _messages.StringField(2)


class UpdateClusterRequest(_messages.Message):
  """UpdateClusterRequest updates a cluster.

  Fields:
    update: A description of the update.
  """

  update = _messages.MessageField('ClusterUpdate', 1)


encoding.AddCustomJsonEnumMapping(
    StandardQueryParameters.FXgafvValueValuesEnum, '_1', '1',
    package=u'container')
encoding.AddCustomJsonEnumMapping(
    StandardQueryParameters.FXgafvValueValuesEnum, '_2', '2',
    package=u'container')
encoding.AddCustomJsonFieldMapping(
    StandardQueryParameters, 'f__xgafv', '$.xgafv',
    package=u'container')
