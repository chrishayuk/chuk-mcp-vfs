"""
Tests for WorkspaceTools
"""

import pytest

from chuk_mcp_vfs.models import ProviderType, WorkspaceCreateRequest
from chuk_mcp_vfs.workspace_manager import WorkspaceManager
from chuk_mcp_vfs.workspace_tools import WorkspaceTools


@pytest.fixture
def workspace_tools():
    """Fixture to create workspace tools for testing."""
    manager = WorkspaceManager()
    tools = WorkspaceTools(manager)
    return tools


@pytest.mark.asyncio
async def test_workspace_create(workspace_tools):
    """Test creating a workspace via tools."""
    request = WorkspaceCreateRequest(name="test-ws", provider=ProviderType.MEMORY)

    response = await workspace_tools.workspace_create(request)

    assert response.name == "test-ws"
    assert response.provider == ProviderType.MEMORY
    assert response.current_path == "/"
    assert not response.is_mounted


@pytest.mark.asyncio
async def test_workspace_list(workspace_tools):
    """Test listing workspaces via tools."""
    # Create some workspaces
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="ws1", provider=ProviderType.MEMORY)
    )
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="ws2", provider=ProviderType.MEMORY)
    )

    response = await workspace_tools.workspace_list()

    assert len(response.workspaces) == 2
    names = {ws.name for ws in response.workspaces}
    assert names == {"ws1", "ws2"}


@pytest.mark.asyncio
async def test_workspace_switch(workspace_tools):
    """Test switching workspaces via tools."""
    # Create workspaces
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="ws1", provider=ProviderType.MEMORY)
    )
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="ws2", provider=ProviderType.MEMORY)
    )

    # Switch to ws2
    response = await workspace_tools.workspace_switch("ws2")

    assert response.name == "ws2"
    assert response.provider == ProviderType.MEMORY


@pytest.mark.asyncio
async def test_workspace_info(workspace_tools):
    """Test getting workspace info via tools."""
    # Create workspace
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="info-test", provider=ProviderType.MEMORY)
    )

    # Get info
    info = await workspace_tools.workspace_info("info-test")

    assert info.name == "info-test"
    assert info.provider_type == ProviderType.MEMORY


@pytest.mark.asyncio
async def test_workspace_destroy(workspace_tools):
    """Test destroying a workspace via tools."""
    # Create workspace
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="destroy-me", provider=ProviderType.MEMORY)
    )

    # Destroy it
    response = await workspace_tools.workspace_destroy("destroy-me")

    assert response.success is True
    assert response.workspace == "destroy-me"

    # Verify it's gone
    list_response = await workspace_tools.workspace_list()
    names = {ws.name for ws in list_response.workspaces}
    assert "destroy-me" not in names


@pytest.mark.asyncio
async def test_workspace_info_current(workspace_tools):
    """Test getting current workspace info."""
    # Create workspace
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="current-ws", provider=ProviderType.MEMORY)
    )

    # Get current workspace info (no name parameter)
    info = await workspace_tools.workspace_info()

    assert info.name == "current-ws"
    assert info.provider_type == ProviderType.MEMORY


@pytest.mark.asyncio
async def test_workspace_mount(workspace_tools):
    """Test mounting a workspace (placeholder implementation)."""
    from chuk_mcp_vfs.models import WorkspaceMountRequest

    # Create workspace
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="mount-test", provider=ProviderType.MEMORY)
    )

    # Try to mount
    request = WorkspaceMountRequest(name="mount-test", mount_point="/tmp/test-mount")
    response = await workspace_tools.workspace_mount(request)

    # Currently returns error about not implemented
    assert response.workspace == "mount-test"
    # Implementation is placeholder, so we just verify it returns


@pytest.mark.asyncio
async def test_workspace_mount_already_mounted(workspace_tools):
    """Test mounting an already-mounted workspace."""
    from chuk_mcp_vfs.models import WorkspaceMountRequest

    # Create workspace
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="mount-test", provider=ProviderType.MEMORY)
    )

    # Mount it
    request = WorkspaceMountRequest(name="mount-test")
    await workspace_tools.workspace_mount(request)

    # Try to mount again
    response = await workspace_tools.workspace_mount(request)

    assert response.success is False
    assert "already mounted" in response.error.lower()


@pytest.mark.asyncio
async def test_workspace_unmount(workspace_tools):
    """Test unmounting a workspace."""
    from chuk_mcp_vfs.models import WorkspaceMountRequest

    # Create and mount workspace
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="unmount-test", provider=ProviderType.MEMORY)
    )

    request = WorkspaceMountRequest(name="unmount-test")
    await workspace_tools.workspace_mount(request)

    # Unmount it
    response = await workspace_tools.workspace_unmount("unmount-test")

    assert response.success is True
    assert response.workspace == "unmount-test"


@pytest.mark.asyncio
async def test_workspace_unmount_not_mounted(workspace_tools):
    """Test unmounting a workspace that isn't mounted."""
    # Create workspace
    await workspace_tools.workspace_create(
        WorkspaceCreateRequest(name="not-mounted", provider=ProviderType.MEMORY)
    )

    # Try to unmount
    response = await workspace_tools.workspace_unmount("not-mounted")

    assert response.success is False
    assert "not mounted" in response.error.lower()
