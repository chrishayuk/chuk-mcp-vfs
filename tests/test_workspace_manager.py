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


@pytest.mark.asyncio
async def test_get_current_path():
    """Test getting current path."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="test-ws", provider_type=ProviderType.MEMORY)

    # Default is /
    assert manager.get_current_path() == "/"

    # Set and get new path
    manager.set_current_path("/new/path")
    assert manager.get_current_path() == "/new/path"


@pytest.mark.asyncio
async def test_get_current_vfs():
    """Test getting current VFS."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="test-ws", provider_type=ProviderType.MEMORY)

    vfs = manager.get_current_vfs()
    assert vfs is not None


@pytest.mark.asyncio
async def test_get_vfs_by_name():
    """Test getting VFS by name."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="ws1", provider_type=ProviderType.MEMORY)
    await manager.create_workspace(name="ws2", provider_type=ProviderType.MEMORY)

    vfs1 = manager.get_vfs("ws1")
    vfs2 = manager.get_vfs("ws2")

    assert vfs1 is not None
    assert vfs2 is not None
    # They should be different VFS instances
    assert vfs1 is not vfs2


@pytest.mark.asyncio
async def test_switch_nonexistent_workspace():
    """Test switching to non-existent workspace raises error."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="ws1", provider_type=ProviderType.MEMORY)

    with pytest.raises(ValueError, match="does not exist"):
        await manager.switch_workspace("nonexistent")


@pytest.mark.asyncio
async def test_destroy_nonexistent_workspace():
    """Test destroying non-existent workspace raises error."""
    manager = WorkspaceManager()

    with pytest.raises(ValueError, match="does not exist"):
        await manager.destroy_workspace("nonexistent")


@pytest.mark.asyncio
async def test_get_workspace_info_current():
    """Test getting current workspace info."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="test", provider_type=ProviderType.MEMORY)

    info = manager.get_workspace_info()
    assert info.name == "test"
    assert info.provider_type == ProviderType.MEMORY


@pytest.mark.asyncio
async def test_get_workspace_info_by_name():
    """Test getting workspace info by name."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="ws1", provider_type=ProviderType.MEMORY)
    await manager.create_workspace(name="ws2", provider_type=ProviderType.MEMORY)

    info = manager.get_workspace_info("ws1")
    assert info.name == "ws1"


@pytest.mark.asyncio
async def test_list_all_namespaces():
    """Test listing all namespaces."""
    from chuk_artifacts import NamespaceType, StorageScope

    manager = WorkspaceManager()

    # Create workspaces with SANDBOX scope so they're always visible
    await manager.create_workspace(
        name="ws1", provider_type=ProviderType.MEMORY, scope=StorageScope.SANDBOX
    )
    await manager.create_workspace(
        name="ws2", provider_type=ProviderType.MEMORY, scope=StorageScope.SANDBOX
    )

    # List all namespaces without filtering
    namespaces = manager.list_all_namespaces()

    # Should have at least the 2 workspaces we created
    assert len(namespaces) >= 2

    # Verify we can filter by type
    workspace_namespaces = manager.list_all_namespaces(type=NamespaceType.WORKSPACE)
    # Should have our workspace namespaces
    assert len(workspace_namespaces) >= 2


@pytest.mark.asyncio
async def test_get_workspace_info_nonexistent():
    """Test getting info for non-existent workspace raises error."""
    manager = WorkspaceManager()

    await manager.create_workspace(name="ws1", provider_type=ProviderType.MEMORY)

    with pytest.raises(ValueError, match="does not exist"):
        manager.get_workspace_info("nonexistent")


@pytest.mark.asyncio
async def test_create_workspace_with_user_scope():
    """Test creating workspace with USER scope."""
    from chuk_artifacts import StorageScope

    manager = WorkspaceManager()

    # Create with USER scope - must provide user_id
    info = await manager.create_workspace(
        name="user-ws",
        provider_type=ProviderType.MEMORY,
        scope=StorageScope.USER,
        user_id="test_user",
    )

    assert info.name == "user-ws"
    assert info.provider_type == ProviderType.MEMORY


@pytest.mark.asyncio
async def test_sync_with_existing_blob_namespace():
    """Test that _sync_namespaces skips non-WORKSPACE namespaces."""
    from chuk_artifacts import NamespaceType, StorageScope

    manager = WorkspaceManager()

    # Create a BLOB namespace (shouldn't be synced as workspace)
    await manager._store.create_namespace(
        type=NamespaceType.BLOB,
        name="blob-ns",
        scope=StorageScope.SANDBOX,
        provider_type="vfs-memory",
    )

    # Create a WORKSPACE namespace (should be synced)
    await manager._store.create_namespace(
        type=NamespaceType.WORKSPACE,
        name="workspace-ns",
        scope=StorageScope.SANDBOX,
        provider_type="vfs-memory",
    )

    # Trigger sync
    await manager._sync_namespaces()

    # Should only have workspace-ns
    workspaces = manager.list_workspaces()
    workspace_names = {ws.name for ws in workspaces}

    assert "workspace-ns" in workspace_names
    assert "blob-ns" not in workspace_names


@pytest.mark.asyncio
async def test_get_workspace_info_no_current():
    """Test getting workspace info when no current workspace."""
    manager = WorkspaceManager()

    # Don't create any workspaces - should have no current workspace
    with pytest.raises(ValueError, match="No current workspace"):
        manager.get_workspace_info()


@pytest.mark.asyncio
async def test_get_current_vfs_no_workspace():
    """Test getting current VFS when no workspace exists."""
    manager = WorkspaceManager()

    with pytest.raises(ValueError, match="No current workspace"):
        manager.get_current_vfs()
