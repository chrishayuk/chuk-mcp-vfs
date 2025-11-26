"""
Checkpoint Manager - Manages checkpoints for workspaces

Wraps the existing AsyncSnapshotManager with checkpoint-specific logic.
"""

from datetime import UTC, datetime

from chuk_virtual_fs.snapshot_manager import AsyncSnapshotManager

from chuk_mcp_vfs.models import CheckpointInfo, ProviderType
from chuk_mcp_vfs.workspace_manager import WorkspaceManager


class CheckpointManager:
    """
    Manages checkpoints for virtual filesystem workspaces.

    Each workspace has its own checkpoint history.
    """

    def __init__(self, workspace_manager: WorkspaceManager):
        self.workspace_manager = workspace_manager
        # Map workspace name to snapshot manager
        self._snapshot_managers: dict[str, AsyncSnapshotManager] = {}

    def _get_snapshot_manager(
        self, workspace_name: str | None = None
    ) -> AsyncSnapshotManager:
        """Get or create snapshot manager for workspace."""
        if workspace_name is None:
            info = self.workspace_manager.get_workspace_info()
            workspace_name = info.name

        if workspace_name not in self._snapshot_managers:
            vfs = self.workspace_manager.get_vfs(workspace_name)
            self._snapshot_managers[workspace_name] = AsyncSnapshotManager(vfs)

        return self._snapshot_managers[workspace_name]

    async def create_checkpoint(
        self, name: str | None = None, description: str = ""
    ) -> CheckpointInfo:
        """
        Create a checkpoint of the current workspace state.

        Args:
            name: Optional checkpoint name (auto-generated if not provided)
            description: Description of the checkpoint

        Returns:
            CheckpointInfo for the created checkpoint
        """
        snapshot_mgr = self._get_snapshot_manager()
        workspace_info = self.workspace_manager.get_workspace_info()

        # Create snapshot
        checkpoint_id = await snapshot_mgr.create_snapshot(
            name=name, description=description
        )

        # Get snapshot metadata
        snapshots = snapshot_mgr.list_snapshots()
        snapshot_meta = next(
            (s for s in snapshots if s["name"] == checkpoint_id), None
        )

        if snapshot_meta is None:
            raise RuntimeError(f"Failed to create checkpoint: {checkpoint_id}")

        return CheckpointInfo(
            id=checkpoint_id,
            name=name,
            description=snapshot_meta.get("description", ""),
            created_at=datetime.fromtimestamp(
                snapshot_meta["created"], tz=UTC
            ),
            workspace=workspace_info.name,
            provider_type=workspace_info.provider_type,
            stats=snapshot_meta.get("stats", {}),
        )

    async def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore workspace to a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to restore

        Returns:
            True if restore was successful

        Raises:
            ValueError: If checkpoint doesn't exist
        """
        snapshot_mgr = self._get_snapshot_manager()
        success = await snapshot_mgr.restore_snapshot(checkpoint_id)

        if not success:
            raise ValueError(f"Checkpoint '{checkpoint_id}' does not exist")

        return success

    async def list_checkpoints(self) -> list[CheckpointInfo]:
        """
        List all checkpoints for the current workspace.

        Returns:
            List of CheckpointInfo objects
        """
        snapshot_mgr = self._get_snapshot_manager()
        workspace_info = self.workspace_manager.get_workspace_info()

        snapshots = snapshot_mgr.list_snapshots()

        checkpoints = []
        for snapshot in snapshots:
            checkpoint = CheckpointInfo(
                id=snapshot["name"],
                name=snapshot.get("name"),
                description=snapshot.get("description", ""),
                created_at=datetime.fromtimestamp(snapshot["created"], tz=UTC),
                workspace=workspace_info.name,
                provider_type=workspace_info.provider_type,
                stats=snapshot.get("stats", {}),
            )
            checkpoints.append(checkpoint)

        return checkpoints

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to delete

        Returns:
            True if checkpoint was deleted

        Raises:
            ValueError: If checkpoint doesn't exist
        """
        snapshot_mgr = self._get_snapshot_manager()
        success = snapshot_mgr.delete_snapshot(checkpoint_id)

        if not success:
            raise ValueError(f"Checkpoint '{checkpoint_id}' does not exist")

        return success
