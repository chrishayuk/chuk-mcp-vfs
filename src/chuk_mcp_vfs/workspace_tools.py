"""
Workspace Tools - MCP tools for workspace lifecycle management

All tools are async native and return Pydantic models.
"""

from chuk_mcp_vfs.models import (
    WorkspaceCreateRequest,
    WorkspaceCreateResponse,
    WorkspaceDestroyResponse,
    WorkspaceInfo,
    WorkspaceListResponse,
    WorkspaceMountRequest,
    WorkspaceMountResponse,
    WorkspaceSwitchResponse,
    WorkspaceUnmountResponse,
)
from chuk_mcp_vfs.workspace_manager import WorkspaceManager


class WorkspaceTools:
    """Collection of workspace management tools for MCP."""

    def __init__(self, workspace_manager: WorkspaceManager):
        self.workspace_manager = workspace_manager

    async def workspace_create(
        self, request: WorkspaceCreateRequest
    ) -> WorkspaceCreateResponse:
        """
        Create a new workspace.

        Args:
            request: WorkspaceCreateRequest with name, provider, template, scope, and config

        Returns:
            WorkspaceCreateResponse with workspace info
        """
        info = await self.workspace_manager.create_workspace(
            name=request.name,
            provider_type=request.provider,
            provider_config=request.provider_config,
            template=request.template,
            scope=request.scope,
        )

        return WorkspaceCreateResponse(
            name=info.name,
            provider=info.provider_type,
            created_at=info.created_at,
            current_path=info.current_path,
            is_mounted=info.is_mounted,
        )

    async def workspace_destroy(self, name: str) -> WorkspaceDestroyResponse:
        """
        Destroy a workspace and clean up all resources.

        Args:
            name: Workspace name

        Returns:
            WorkspaceDestroyResponse with success status
        """
        await self.workspace_manager.destroy_workspace(name)

        return WorkspaceDestroyResponse(success=True, workspace=name)

    async def workspace_list(self) -> WorkspaceListResponse:
        """
        List all workspaces.

        Returns:
            WorkspaceListResponse with list of workspaces
        """
        # Sync with namespaces first
        await self.workspace_manager._sync_namespaces()
        workspaces = self.workspace_manager.list_workspaces()

        return WorkspaceListResponse(workspaces=workspaces)

    async def workspace_switch(self, name: str) -> WorkspaceSwitchResponse:
        """
        Switch to a different workspace.

        Args:
            name: Workspace name to switch to

        Returns:
            WorkspaceSwitchResponse with new current workspace info
        """
        info = await self.workspace_manager.switch_workspace(name)

        return WorkspaceSwitchResponse(
            name=info.name,
            provider=info.provider_type,
            current_path=info.current_path,
            is_mounted=info.is_mounted,
        )

    async def workspace_info(self, name: str | None = None) -> WorkspaceInfo:
        """
        Get detailed information about a workspace.

        Args:
            name: Workspace name (None for current workspace)

        Returns:
            WorkspaceInfo with full workspace details
        """
        return self.workspace_manager.get_workspace_info(name)

    async def workspace_mount(
        self, request: WorkspaceMountRequest
    ) -> WorkspaceMountResponse:
        """
        Mount workspace via FUSE.

        Args:
            request: WorkspaceMountRequest with name and optional mount_point

        Returns:
            WorkspaceMountResponse with mount info

        Note:
            Requires FUSE support to be installed (pyfuse3 or winfspy)
        """
        info = self.workspace_manager.get_workspace_info(request.name)

        if info.is_mounted:
            return WorkspaceMountResponse(
                success=False,
                workspace=info.name,
                mount_point=info.mount_point,
                error=f"Workspace '{info.name}' is already mounted at {info.mount_point}",
            )

        mount_point = request.mount_point
        if mount_point is None:
            mount_point = f"/tmp/vfs-mounts/{info.name}"

        # TODO: Implement FUSE mounting
        # For now, just update the info
        info.mount_point = mount_point
        info.is_mounted = True

        return WorkspaceMountResponse(
            success=True,
            workspace=info.name,
            mount_point=mount_point,
            error="FUSE mounting not yet implemented - placeholder only",
        )

    async def workspace_unmount(
        self, name: str | None = None
    ) -> WorkspaceUnmountResponse:
        """
        Unmount workspace.

        Args:
            name: Workspace name (None for current)

        Returns:
            WorkspaceUnmountResponse with success status
        """
        info = self.workspace_manager.get_workspace_info(name)

        if not info.is_mounted:
            return WorkspaceUnmountResponse(
                success=False,
                workspace=info.name,
                error=f"Workspace '{info.name}' is not mounted",
            )

        # TODO: Implement FUSE unmounting
        info.is_mounted = False
        mount_point = info.mount_point
        info.mount_point = None

        return WorkspaceUnmountResponse(
            success=True, workspace=info.name, mount_point=mount_point
        )
