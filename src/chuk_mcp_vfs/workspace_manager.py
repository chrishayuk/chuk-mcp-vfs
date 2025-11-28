"""
Workspace Manager - Manages workspaces via unified namespace architecture

This is a thin wrapper around chuk-artifacts that provides:
- Workspace tracking and switching
- Current working directory per workspace
- Context-aware namespace management (using user_id/session_id from context)
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from chuk_artifacts import ArtifactStore, NamespaceInfo, NamespaceType, StorageScope
from chuk_mcp_server.context import get_session_id, get_user_id
from chuk_virtual_fs import AsyncVirtualFileSystem

from chuk_mcp_vfs.models import ProviderType, WorkspaceInfo


class WorkspaceManager:
    """
    Manages workspaces via the unified namespace architecture.

    Each workspace is a WORKSPACE-type namespace in chuk-artifacts.
    The manager tracks which workspace is current and provides convenience
    methods for path resolution and working directory management.
    """

    def __init__(self, artifact_store: ArtifactStore | None = None) -> None:
        """
        Initialize workspace manager.

        Args:
            artifact_store: Optional ArtifactStore instance (auto-created if None)
        """
        self._store = artifact_store or ArtifactStore()
        self._namespace_to_info: dict[str, WorkspaceInfo] = {}
        self._current_namespace_id: str | None = None
        self._lock = asyncio.Lock()
        self._initialized = False

    def _provider_type_to_vfs_type(self, provider_type: ProviderType) -> str:
        """Convert ProviderType enum to VFS provider string."""
        mapping = {
            ProviderType.MEMORY: "vfs-memory",
            ProviderType.FILESYSTEM: "vfs-filesystem",
            ProviderType.SQLITE: "vfs-sqlite",
            ProviderType.S3: "vfs-s3",
        }
        return mapping[provider_type]

    def _vfs_type_to_provider_type(self, vfs_type: str) -> ProviderType:
        """Convert VFS provider string to ProviderType enum."""
        mapping = {
            "vfs-memory": ProviderType.MEMORY,
            "vfs-filesystem": ProviderType.FILESYSTEM,
            "vfs-sqlite": ProviderType.SQLITE,
            "vfs-s3": ProviderType.S3,
        }
        return mapping.get(vfs_type, ProviderType.MEMORY)

    async def create_workspace(
        self,
        name: str,
        provider_type: ProviderType = ProviderType.MEMORY,
        provider_config: dict[str, Any] | None = None,
        template: str | None = None,
        scope: StorageScope = StorageScope.SESSION,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> WorkspaceInfo:
        """
        Create a new workspace using the unified namespace architecture.

        Args:
            name: Workspace name
            provider_type: Storage provider type
            provider_config: Provider-specific configuration
            template: Optional template to initialize from
            scope: Storage scope (SESSION, USER, or SANDBOX)
            user_id: User ID (auto-detected from context if None)
            session_id: Session ID (auto-detected from context if None)

        Returns:
            WorkspaceInfo for the created workspace

        Raises:
            ValueError: If workspace name already exists in current scope
        """
        async with self._lock:
            # Sync with existing namespaces first
            await self._sync_namespaces()

            # Get user_id and session_id from context if not provided
            if user_id is None and scope in (StorageScope.USER, StorageScope.SESSION):
                try:
                    user_id = get_user_id()
                except Exception:
                    user_id = "default"

            if session_id is None and scope == StorageScope.SESSION:
                try:
                    session_id = get_session_id()
                except Exception:
                    session_id = None

            # Check if workspace with this name already exists in this scope
            existing = self.list_workspaces()
            for ws in existing:
                if ws.name == name:
                    raise ValueError(f"Workspace '{name}' already exists")

            # Create namespace
            vfs_type = self._provider_type_to_vfs_type(provider_type)
            config = provider_config or {}

            namespace_info = await self._store.create_namespace(
                type=NamespaceType.WORKSPACE,
                name=name,
                scope=scope,
                user_id=user_id,
                session_id=session_id,
                provider_type=vfs_type,
                provider_config=config,
            )

            # Apply template if specified
            if template:
                vfs = self._store.get_namespace_vfs(namespace_info.namespace_id)
                await self._apply_template(vfs, template)

            # Create workspace info
            info = WorkspaceInfo(
                name=name,
                provider_type=provider_type,
                created_at=namespace_info.created_at,
                current_path="/",
                metadata={
                    "namespace_id": namespace_info.namespace_id,
                    "scope": scope.value,
                    "provider_config": config,
                },
            )

            self._namespace_to_info[namespace_info.namespace_id] = info

            # Set as current if first workspace
            if self._current_namespace_id is None:
                self._current_namespace_id = namespace_info.namespace_id

            return info

    async def destroy_workspace(self, name: str) -> None:
        """
        Destroy a workspace and clean up resources.

        Args:
            name: Workspace name

        Raises:
            ValueError: If workspace doesn't exist
        """
        async with self._lock:
            # Find namespace by name
            namespace_id = None
            for nid, info in self._namespace_to_info.items():
                if info.name == name:
                    namespace_id = nid
                    break

            if namespace_id is None:
                raise ValueError(f"Workspace '{name}' does not exist")

            # Destroy namespace
            await self._store.destroy_namespace(namespace_id)

            # Remove from tracking
            del self._namespace_to_info[namespace_id]

            # Switch to another workspace if current was destroyed
            if self._current_namespace_id == namespace_id:
                self._current_namespace_id = (
                    next(iter(self._namespace_to_info.keys()))
                    if self._namespace_to_info
                    else None
                )

    async def _sync_namespaces(self) -> None:
        """Sync workspace tracking with existing namespaces from artifact store."""
        if self._initialized:
            return

        # Get all workspace-type namespaces from the store
        namespaces = self.list_all_namespaces()

        for ns_info in namespaces:
            if ns_info.type != NamespaceType.WORKSPACE:
                continue

            # Convert namespace to workspace info
            provider_type = self._vfs_type_to_provider_type(
                ns_info.provider_type or "vfs-memory"
            )

            # Skip if no name (shouldn't happen for WORKSPACE type, but be defensive)
            if not ns_info.name:
                continue

            workspace_info = WorkspaceInfo(
                name=ns_info.name,
                provider_type=provider_type,
                created_at=datetime.fromisoformat(ns_info.created_at),
                current_path="/",
                metadata={
                    "namespace_id": ns_info.namespace_id,
                    "scope": ns_info.scope.value if ns_info.scope else "session",
                },
            )

            self._namespace_to_info[ns_info.namespace_id] = workspace_info

        # Set first workspace as current if available
        if self._namespace_to_info and self._current_namespace_id is None:
            self._current_namespace_id = next(iter(self._namespace_to_info.keys()))

        self._initialized = True

    def list_workspaces(self) -> list[WorkspaceInfo]:
        """List all tracked workspaces."""
        return list(self._namespace_to_info.values())

    def list_all_namespaces(
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        type: NamespaceType | None = None,
    ) -> "list[NamespaceInfo]":
        """
        List all namespaces from artifact store.

        Args:
            user_id: Filter by user (auto-detected from context if None)
            session_id: Filter by session (auto-detected from context if None)
            type: Filter by namespace type (WORKSPACE or BLOB)

        Returns:
            List of NamespaceInfo objects
        """
        # Get from context if not provided
        if user_id is None:
            try:
                user_id = get_user_id()
            except Exception:
                user_id = None

        if session_id is None:
            try:
                session_id = get_session_id()
            except Exception:
                session_id = None

        return self._store.list_namespaces(  # type: ignore[no-any-return]
            user_id=user_id,
            session_id=session_id,
            type=type,
        )

    async def switch_workspace(self, name: str) -> WorkspaceInfo:
        """
        Switch to a different workspace.

        Args:
            name: Workspace name

        Returns:
            WorkspaceInfo for the switched workspace

        Raises:
            ValueError: If workspace doesn't exist
        """
        # Find namespace by name
        for nid, info in self._namespace_to_info.items():
            if info.name == name:
                self._current_namespace_id = nid
                return info

        raise ValueError(f"Workspace '{name}' does not exist")

    def get_workspace_info(self, name: str | None = None) -> WorkspaceInfo:
        """
        Get workspace information.

        Args:
            name: Workspace name (None for current workspace)

        Returns:
            WorkspaceInfo

        Raises:
            ValueError: If workspace doesn't exist or no current workspace
        """
        if name is None:
            if self._current_namespace_id is None:
                raise ValueError("No current workspace")
            return self._namespace_to_info[self._current_namespace_id]

        # Find by name
        for info in self._namespace_to_info.values():
            if info.name == name:
                return info

        raise ValueError(f"Workspace '{name}' does not exist")

    def get_current_vfs(self) -> AsyncVirtualFileSystem:
        """
        Get the VFS for the current workspace.

        Returns:
            AsyncVirtualFileSystem instance

        Raises:
            ValueError: If no current workspace
        """
        if self._current_namespace_id is None:
            raise ValueError("No current workspace")

        return self._store.get_namespace_vfs(self._current_namespace_id)  # type: ignore[no-any-return]

    def get_vfs(self, name: str) -> AsyncVirtualFileSystem:
        """
        Get VFS for a specific workspace.

        Args:
            name: Workspace name

        Returns:
            AsyncVirtualFileSystem instance

        Raises:
            ValueError: If workspace doesn't exist
        """
        # Find namespace by name
        for nid, info in self._namespace_to_info.items():
            if info.name == name:
                return self._store.get_namespace_vfs(nid)  # type: ignore[no-any-return]

        raise ValueError(f"Workspace '{name}' does not exist")

    def get_current_namespace_id(self) -> str | None:
        """Get the current namespace ID."""
        return self._current_namespace_id

    def get_current_path(self, workspace: str | None = None) -> str:
        """Get current working directory for workspace."""
        info = self.get_workspace_info(workspace)
        return info.current_path

    def set_current_path(self, path: str, workspace: str | None = None) -> None:
        """Set current working directory for workspace."""
        info = self.get_workspace_info(workspace)
        info.current_path = path

    def resolve_path(self, path: str, workspace: str | None = None) -> str:
        """
        Resolve a path relative to current working directory.

        Args:
            path: Path (absolute or relative)
            workspace: Workspace name (None for current)

        Returns:
            Absolute path
        """
        if path.startswith("/"):
            return path

        current = self.get_current_path(workspace)
        return str(Path(current) / path)

    async def _apply_template(self, vfs: AsyncVirtualFileSystem, template: str) -> None:
        """
        Apply a template to a VFS.

        Args:
            vfs: VFS instance
            template: Template name

        TODO: Integrate with chuk_virtual_fs.template_loader
        """
        # Placeholder for template application
        # Will integrate with existing template system
        pass
