# Copyright 2015 Google Inc. All Rights Reserved.

"""Source apis layer."""

from googlecloudsdk.core import properties
from googlecloudsdk.third_party.apis.source.v1 import source_v1_messages as messages
from googlecloudsdk.third_party.apis.source.v1.source_v1_client import SourceV1 as client
from googlecloudsdk.dataflow.lib import list_pager


class Source(object):
  """Base class for source api wrappers."""
  _client = None
  _resource_parser = None

  @classmethod
  def SetApiEndpoint(cls, http, endpoint):
    cls._client = client(url=endpoint, get_credentials=False, http=http)

  @classmethod
  def SetResourceParser(cls, parser):
    cls._resource_parser = parser


class Project(Source):
  """Abstracts source project."""

  def __init__(self, project_id):
    self.id = project_id

  def GetRepoList(self):
    """Returns list of repos."""
    request = messages.SourceProjectsReposListRequest(projectId=self.id)
    return self._client.projects_repos.List(request).repos

  def CreateRepo(self, repo_name):
    request = messages.Repo(
        projectId=self.id,
        name=repo_name,
        vcs=messages.Repo.VcsValueValuesEnum.GIT)
    return self._client.projects_repos.Create(request)


class Repo(Source):
  """Abstracts a source repository.

  TODO(user) Increase coverage of the API.
  """

  def __init__(self, project_id, name=''):
    """Initialize to wrap the given repo in a project.

    Args:
      project_id: (string) The id of the project.
      name: (string) The name of the repo. If not specified, use the default
        repo for the project.
    """
    self._repo_name = name
    self._project_id = project_id

  def ListRevisions(
      self, starts=None, ends=None, path=None,
      walk_direction=messages.SourceProjectsReposRevisionsListRequest.
      WalkDirectionValueValuesEnum.FORWARD):
    """Request a list of revisions.

    Args:
      starts: ([string])
        Revision IDs (hexadecimal strings) that specify where the listing
        begins. If empty, the repo heads (revisions with no children) are
        used.
      ends: ([string])
        Revision IDs (hexadecimal strings) that specify where the listing
        ends. If this field is present, the listing will contain only
        revisions that are topologically between starts and ends, inclusive.
      path: (string)
        List only those revisions that modify path.
      walk_direction: (messages.SourceProjectsReposRevisionsListRequest.
                       WalkDirectionValueValuesEnum)
        The direction to walk the graph.
    Returns:
      [messages.Revision] The revisions matching the search criteria, in the
      order specified by walkDirection.
    """
    if not starts:
      starts = []
    if not ends:
      ends = []
    request = messages.SourceProjectsReposRevisionsListRequest(
        projectId=self._project_id, repoName=self._repo_name,
        starts=starts, ends=ends, path=path, walkDirection=walk_direction)

    return list_pager.YieldFromList(
        self._client.projects_repos_revisions,
        request,
        field='revisions')

  def ListAliases(self, kind=messages.SourceProjectsReposAliasesListRequest.
                  KindValueValuesEnum.MOVABLE):
    """Request a list of aliases.

    Args:
      kind: (messages.SourceProjectsReposAliasesListRequest.KindValueValuesEnum)
        The type of alias to list (fixed, movable, etc).
    Returns:
      [messages.Alias] The aliases of the given kind.
    """
    request = messages.SourceProjectsReposAliasesListRequest(
        projectId=self._project_id, repoName=self._repo_name, kind=kind)

    return list_pager.YieldFromList(
        self._client.projects_repos_aliases,
        request,
        field='aliases')

  def ListWorkspaces(self):
    """Request a list of workspaces.

    Yields:
      (Workspace) The list of workspaces.
    """
    request = messages.SourceProjectsReposWorkspacesListRequest(
        projectId=self._project_id, repoName=self._repo_name)
    response = self._client.projects_repos_workspaces.List(request)
    for ws in response.workspaces:
      yield Workspace(self._project_id, ws.id.name, repo_name=self._repo_name,
                      state=ws)

  def CreateAlias(self, name, revision_id, kind):
    """Create a new alias (branch) in the repo.

    Args:
      name: (string) The name of the branch.
      revision_id: (string) The ID of the revision.
      kind: (messages.Alias.KindValueValuesEnum) The type of alias.
    Returns:
      (messages.Alias) The alias that was created.
    """
    request = messages.SourceProjectsReposAliasesCreateRequest(
        projectId=self._project_id, repoName=self._repo_name,
        alias=messages.Alias(name=name, revisionId=revision_id, kind=kind))
    return self._client.projects_repos_aliases.Create(request)

  def CreateWorkspace(self, workspace_name, alias_name, expected_baseline=None):
    """Create a new workspace in the repo.

    Args:
      workspace_name: (string) The name of the new workspace. Must be unique.
      alias_name: (string) The alias to use as a baseline for the workspace.
        If the alias does not exist, the workspace will have no baseline, and
        when it is commited, this name will be used to create a new movable
        alias referring to the new root revision created by this workspace.
      expected_baseline: (string) The expected current revision ID for the
        alias specified by alias_name. If specified, this value must match the
        alias's current revision ID at the time CreateWorkspace is called.
    Returns:
      (Workspace) The workspace that was created.
    """
    request = messages.SourceProjectsReposWorkspacesCreateRequest(
        projectId=self._project_id, repoName=self._repo_name,
        createWorkspaceRequest=messages.CreateWorkspaceRequest(
            workspace=messages.Workspace(
                id=messages.CloudWorkspaceId(name=workspace_name),
                alias=alias_name,
                baseline=expected_baseline)))
    return Workspace(
        self._project_id, workspace_name, repo_name=self._repo_name,
        state=self._client.projects_repos_workspaces.Create(request))

  def DeleteWorkspace(self, workspace_name, current_snapshot=None):
    """Delete a workspace from the repo.

    Args:
      workspace_name: (string) The name of the new workspace. Must be unique.
      current_snapshot: (string) The current snapshot ID of the workspace,
        used to verify that the workspace hasn't changed. If not None, the
        delete will succeed if and only if the snapshot ID of the workspace
        matches this value.
    """
    request = messages.SourceProjectsReposWorkspacesDeleteRequest(
        projectId=self._project_id, repoName=self._repo_name,
        name=workspace_name, currentSnapshotId=current_snapshot)
    self._client.projects_repos_workspaces.Delete(request)


class Workspace(Source):
  """Abstracts a workspace."""

  # Maximum amount of data to buffer.
  # TODO(user) Determine the actual POST size limit
  SIZE_THRESHOLD = 0x200000

  def __init__(self, project_id, workspace_name, repo_name='', state=None):
    """Initialize from a workspace message.

    Args:
      project_id: (string) The project ID for the workspace.
      workspace_name: (string) The name of the workspace
      repo_name: (string) The repo containing the workspace. If not specified,
        use the default repo for the project.
      state: (messages.Workspace) Server-supplied workspace information.
        Since this argument usually comes from a call to the server, the repo
        will usually be specified by a uid rather than a name.
    """
    self._project_id = project_id
    self._repo_name = repo_name
    self._workspace_name = workspace_name
    self._pending_actions = []
    self._workspace_state = state
    self._post_callback = None

  def SetPostCallback(self, callback):
    """Sets a notification function to be called when actions are posted.

    Args:
      callback: (lambda(int)) A function to call with the number of actions
        posted to the server after the workspace has been modified.
    """

    self._post_callback = callback

  def FlushPendingActions(self, check_size_threshold=False):
    """Flushes all pending actions.

    Args:
      check_size_threshold: (boolean) If true, check if the total size of the
        contents of all pending actions exceeds SIZE_THRESHOLD
    """

    if not self._pending_actions:
      return
    if check_size_threshold:
      total = 0
      for a in self._pending_actions:
        if a.writeAction:
          total += len(a.writeAction.contents) + len(a.writeAction.path)
      if total < self.SIZE_THRESHOLD:
        return
    request = messages.SourceProjectsReposWorkspacesModifyWorkspaceRequest(
        projectId=self._project_id, repoName=self._repo_name,
        name=self._workspace_name,
        modifyWorkspaceRequest=messages.ModifyWorkspaceRequest(
            actions=self._pending_actions))
    self._workspace_state = (
        self._client.projects_repos_workspaces.ModifyWorkspace(request))
    if self._post_callback:
      self._post_callback(len(self._pending_actions))
    self._pending_actions = []

  def Commit(self, message, paths=None):
    """Commit all pending changes to the repo.

    Args:
      message: (string) A description of the commit.
      paths: ([string]) Restrict the commit to the given paths.
    Returns:
      A messages.Workspace object describing the state after the commit.
    """

    self.FlushPendingActions()
    current_snapshot = None
    if self._workspace_state:
      current_snapshot = self._workspace_state.currentSnapshotId
    if not paths:
      paths = []
    request = messages.SourceProjectsReposWorkspacesCommitWorkspaceRequest(
        projectId=self._project_id, repoName=self._repo_name,
        name=self._workspace_name,
        commitWorkspaceRequest=messages.CommitWorkspaceRequest(
            author=properties.VALUES.core.account.Get(required=True),
            currentSnapshotId=current_snapshot,
            message=message,
            paths=paths))
    self._workspace_state = (
        self._client.projects_repos_workspaces.CommitWorkspace(request))
    return self._workspace_state

  def WriteFile(self, path, contents,
                mode=messages.WriteAction.ModeValueValuesEnum.NORMAL):
    """Schedule an action to create or modify a file.

    Args:
      path: The path of the file to write.
      contents: The new contents of the file.
      mode: The new mode of the file.
    """

    # TODO(user) Don't schedule files whose size exceeds SIZE_THRESHOLD
    self._pending_actions.append(messages.Action(
        writeAction=messages.WriteAction(
            path=path, contents=contents, mode=mode)))
    self.FlushPendingActions(check_size_threshold=True)
