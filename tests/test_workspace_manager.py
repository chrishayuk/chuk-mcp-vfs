"""
Tests for WorkspaceManager
"""

import pytest

from chuk_mcp_vfs.models import ProviderType
from chuk_mcp_vfs.workspace_manager import WorkspaceManager


@pytest.mark.asyncio
async def test_create_workspace():
    """Test creating a workspace."""
    manager = WorkspaceManager()

    info = await manager.create_workspace(
        name="test-ws", provider_type=ProviderType.MEMORY
    )

    assert info.name == "test-ws"
    assert info.provider_type == ProviderType.MEMORY
    assert info.current_path == "/"
    assert not info.is_mounted


@pytest.mark.asyncio
async def test_create_duplicate_workspace():
    """Test that creating duplicate workspace fails."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="test-ws", provider_type=ProviderType.MEMORY)

    with pytest.raises(ValueError, match="already exists"):
        await manager.create_workspace(
            name="test-ws", provider_type=ProviderType.MEMORY
        )


@pytest.mark.asyncio
async def test_list_workspaces():
    """Test listing workspaces."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="ws1", provider_type=ProviderType.MEMORY)
    await manager.create_workspace(name="ws2", provider_type=ProviderType.MEMORY)

    workspaces = manager.list_workspaces()

    assert len(workspaces) == 2
    names = {ws.name for ws in workspaces}
    assert names == {"ws1", "ws2"}


@pytest.mark.asyncio
async def test_switch_workspace():
    """Test switching between workspaces."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="ws1", provider_type=ProviderType.MEMORY)
    await manager.create_workspace(name="ws2", provider_type=ProviderType.MEMORY)

    # Initially on ws1 (first created)
    info = manager.get_workspace_info()
    assert info.name == "ws1"

    # Switch to ws2
    info = await manager.switch_workspace("ws2")
    assert info.name == "ws2"

    # Verify current workspace changed
    info = manager.get_workspace_info()
    assert info.name == "ws2"


@pytest.mark.asyncio
async def test_destroy_workspace():
    """Test destroying a workspace."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="test-ws", provider_type=ProviderType.MEMORY)

    assert len(manager.list_workspaces()) == 1

    await manager.destroy_workspace("test-ws")

    assert len(manager.list_workspaces()) == 0


@pytest.mark.asyncio
async def test_resolve_path():
    """Test path resolution."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="test-ws", provider_type=ProviderType.MEMORY)

    # Absolute path stays the same
    assert manager.resolve_path("/foo/bar") == "/foo/bar"

    # Relative path from root
    assert manager.resolve_path("foo") == "/foo"

    # Change directory and test relative path
    manager.set_current_path("/home/user")
    assert manager.resolve_path("documents") == "/home/user/documents"
