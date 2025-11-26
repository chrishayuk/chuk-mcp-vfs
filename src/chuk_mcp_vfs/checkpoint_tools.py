"""
Checkpoint Tools - MCP tools for checkpoint/restore operations

All tools are async native and return Pydantic models.
"""

from datetime import UTC, datetime

from chuk_mcp_vfs.checkpoint_manager import CheckpointManager
from chuk_mcp_vfs.models import (
    CheckpointCreateRequest,
    CheckpointCreateResponse,
    CheckpointListResponse,
    CheckpointRestoreRequest,
    CheckpointRestoreResponse,
)


class CheckpointTools:
    """Collection of checkpoint management tools for MCP."""

    def __init__(self, checkpoint_manager: CheckpointManager):
        self.checkpoint_manager = checkpoint_manager

    async def checkpoint_create(
        self, request: CheckpointCreateRequest
    ) -> CheckpointCreateResponse:
        """
        Create a checkpoint of the current workspace state.

        Args:
            request: CheckpointCreateRequest with name and description

        Returns:
            CheckpointCreateResponse with checkpoint info
        """
        checkpoint_info = await self.checkpoint_manager.create_checkpoint(
            name=request.name, description=request.description
        )

        return CheckpointCreateResponse(
            success=True,
            checkpoint_id=checkpoint_info.id,
            created_at=checkpoint_info.created_at,
        )

    async def checkpoint_restore(
        self, request: CheckpointRestoreRequest
    ) -> CheckpointRestoreResponse:
        """
        Restore workspace to a checkpoint.

        Args:
            request: CheckpointRestoreRequest with checkpoint_id

        Returns:
            CheckpointRestoreResponse with success status
        """
        await self.checkpoint_manager.restore_checkpoint(request.checkpoint_id)

        return CheckpointRestoreResponse(
            success=True,
            checkpoint_id=request.checkpoint_id,
            restored_at=datetime.now(UTC),
        )

    async def checkpoint_list(self) -> CheckpointListResponse:
        """
        List all checkpoints for the current workspace.

        Returns:
            CheckpointListResponse with list of checkpoints
        """
        checkpoints = await self.checkpoint_manager.list_checkpoints()

        return CheckpointListResponse(checkpoints=checkpoints)

    async def checkpoint_delete(self, checkpoint_id: str) -> CheckpointRestoreResponse:
        """
        Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to delete

        Returns:
            Response with success status
        """
        await self.checkpoint_manager.delete_checkpoint(checkpoint_id)

        return CheckpointRestoreResponse(
            success=True,
            checkpoint_id=checkpoint_id,
            restored_at=datetime.now(UTC),
        )
