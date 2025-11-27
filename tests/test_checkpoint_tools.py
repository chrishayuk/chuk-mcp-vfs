"""
Tests for CheckpointTools
"""

import pytest

from chuk_mcp_vfs.checkpoint_manager import CheckpointManager
from chuk_mcp_vfs.checkpoint_tools import CheckpointTools
from chuk_mcp_vfs.models import (
    CheckpointCreateRequest,
    CheckpointRestoreRequest,
    ProviderType,
)
from chuk_mcp_vfs.workspace_manager import WorkspaceManager


@pytest.fixture
async def checkpoint_tools():
    """Fixture to create checkpoint tools for testing."""
    workspace_mgr = WorkspaceManager()
    await workspace_mgr.create_workspace(name="test", provider_type=ProviderType.MEMORY)
    checkpoint_mgr = CheckpointManager(workspace_mgr)
    tools = CheckpointTools(checkpoint_mgr)
    return tools


@pytest.mark.asyncio
async def test_checkpoint_create(checkpoint_tools):
    """Test creating a checkpoint via tools."""
    request = CheckpointCreateRequest(
        name="tool-checkpoint", description="Created via tools"
    )

    response = await checkpoint_tools.checkpoint_create(request)

    assert response.success is True
    assert response.checkpoint_id is not None
    assert response.created_at is not None


@pytest.mark.asyncio
async def test_checkpoint_list(checkpoint_tools):
    """Test listing checkpoints via tools."""
    # Create some checkpoints
    await checkpoint_tools.checkpoint_create(
        CheckpointCreateRequest(name="cp1", description="First")
    )
    await checkpoint_tools.checkpoint_create(
        CheckpointCreateRequest(name="cp2", description="Second")
    )

    response = await checkpoint_tools.checkpoint_list()

    assert len(response.checkpoints) == 2


@pytest.mark.asyncio
async def test_checkpoint_restore(checkpoint_tools):
    """Test restoring a checkpoint via tools."""
    # Create checkpoint
    create_response = await checkpoint_tools.checkpoint_create(
        CheckpointCreateRequest(name="restore-cp", description="Test restore")
    )

    # Restore checkpoint
    restore_request = CheckpointRestoreRequest(
        checkpoint_id=create_response.checkpoint_id
    )
    restore_response = await checkpoint_tools.checkpoint_restore(restore_request)

    assert restore_response.success is True
    assert restore_response.checkpoint_id == create_response.checkpoint_id


@pytest.mark.asyncio
async def test_checkpoint_delete(checkpoint_tools):
    """Test deleting a checkpoint via tools."""
    # Create checkpoint
    create_response = await checkpoint_tools.checkpoint_create(
        CheckpointCreateRequest(name="delete-cp", description="Test delete")
    )

    # Delete checkpoint
    delete_response = await checkpoint_tools.checkpoint_delete(
        create_response.checkpoint_id
    )

    assert delete_response.success is True

    # Verify it's deleted
    list_response = await checkpoint_tools.checkpoint_list()
    assert len(list_response.checkpoints) == 0
