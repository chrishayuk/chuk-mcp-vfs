"""
Tests for CheckpointManager
"""

import pytest

from chuk_mcp_vfs.checkpoint_manager import CheckpointManager
from chuk_mcp_vfs.models import ProviderType
from chuk_mcp_vfs.workspace_manager import WorkspaceManager


@pytest.fixture
async def checkpoint_manager():
    """Fixture to create a checkpoint manager for testing."""
    workspace_mgr = WorkspaceManager()
    await workspace_mgr.create_workspace(name="test", provider_type=ProviderType.MEMORY)
    mgr = CheckpointManager(workspace_mgr)
    return mgr


@pytest.mark.asyncio
async def test_create_checkpoint(checkpoint_manager):
    """Test creating a checkpoint."""
    checkpoint_info = await checkpoint_manager.create_checkpoint(
        name="test-checkpoint", description="Test checkpoint"
    )

    assert checkpoint_info.name == "test-checkpoint"
    assert checkpoint_info.description == "Test checkpoint"
    assert checkpoint_info.workspace == "test"
    assert checkpoint_info.provider_type == ProviderType.MEMORY


@pytest.mark.asyncio
async def test_create_checkpoint_auto_name(checkpoint_manager):
    """Test creating a checkpoint with auto-generated name."""
    checkpoint_info = await checkpoint_manager.create_checkpoint(
        description="Auto-named checkpoint"
    )

    assert checkpoint_info.id is not None
    assert checkpoint_info.description == "Auto-named checkpoint"
    assert checkpoint_info.workspace == "test"


@pytest.mark.asyncio
async def test_list_checkpoints(checkpoint_manager):
    """Test listing checkpoints."""
    # Create multiple checkpoints
    await checkpoint_manager.create_checkpoint(name="checkpoint1", description="First")
    await checkpoint_manager.create_checkpoint(name="checkpoint2", description="Second")

    checkpoints = await checkpoint_manager.list_checkpoints()

    assert len(checkpoints) == 2
    names = {cp.name for cp in checkpoints}
    assert "checkpoint1" in names
    assert "checkpoint2" in names


@pytest.mark.asyncio
async def test_restore_checkpoint(checkpoint_manager):
    """Test restoring a checkpoint."""
    # Create checkpoint
    checkpoint_info = await checkpoint_manager.create_checkpoint(
        name="restore-test", description="Test restore"
    )

    # Restore checkpoint
    success = await checkpoint_manager.restore_checkpoint(checkpoint_info.id)

    assert success is True


@pytest.mark.asyncio
async def test_restore_nonexistent_checkpoint(checkpoint_manager):
    """Test restoring a non-existent checkpoint raises error."""
    with pytest.raises(ValueError, match="does not exist"):
        await checkpoint_manager.restore_checkpoint("nonexistent-checkpoint")


@pytest.mark.asyncio
async def test_delete_checkpoint(checkpoint_manager):
    """Test deleting a checkpoint."""
    # Create checkpoint
    checkpoint_info = await checkpoint_manager.create_checkpoint(
        name="delete-test", description="Test delete"
    )

    # Delete checkpoint
    success = await checkpoint_manager.delete_checkpoint(checkpoint_info.id)

    assert success is True

    # Verify it's deleted
    checkpoints = await checkpoint_manager.list_checkpoints()
    assert len(checkpoints) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_checkpoint(checkpoint_manager):
    """Test deleting a non-existent checkpoint raises error."""
    with pytest.raises(ValueError, match="does not exist"):
        await checkpoint_manager.delete_checkpoint("nonexistent-checkpoint")
