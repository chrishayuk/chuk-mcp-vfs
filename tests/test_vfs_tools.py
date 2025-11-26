"""
Tests for VFS Tools
"""

import pytest

from chuk_mcp_vfs.models import ProviderType, WriteRequest
from chuk_mcp_vfs.vfs_tools import VFSTools
from chuk_mcp_vfs.workspace_manager import WorkspaceManager


@pytest.fixture
async def setup_workspace():
    """Fixture to create a workspace for testing."""
    manager = WorkspaceManager()
    await manager.create_workspace(name="test", provider_type=ProviderType.MEMORY)
    tools = VFSTools(manager)
    return tools


@pytest.mark.asyncio
async def test_write_and_read(setup_workspace):
    """Test writing and reading a file."""
    tools = await setup_workspace

    # Write file
    write_resp = await tools.write(WriteRequest(path="/test.txt", content="Hello World"))
    assert write_resp.success
    assert write_resp.path == "/test.txt"

    # Read file
    read_resp = await tools.read("/test.txt")
    assert read_resp.content == "Hello World"
    assert read_resp.path == "/test.txt"


@pytest.mark.asyncio
async def test_mkdir_and_ls(setup_workspace):
    """Test creating directory and listing."""
    tools = await setup_workspace

    # Create directory
    mkdir_resp = await tools.mkdir("/testdir")
    assert mkdir_resp.success
    assert mkdir_resp.path == "/testdir"

    # List root
    ls_resp = await tools.ls("/")
    assert len(ls_resp.entries) == 1
    assert ls_resp.entries[0].name == "testdir"
    assert ls_resp.entries[0].type.value == "directory"


@pytest.mark.asyncio
async def test_cd_and_pwd(setup_workspace):
    """Test changing directory and getting working directory."""
    tools = await setup_workspace

    # Create directory
    await tools.mkdir("/testdir")

    # Change directory
    cd_resp = await tools.cd("/testdir")
    assert cd_resp.success
    assert cd_resp.cwd == "/testdir"

    # Get current directory
    pwd_resp = await tools.pwd()
    assert pwd_resp.cwd == "/testdir"


@pytest.mark.asyncio
async def test_tree(setup_workspace):
    """Test tree structure."""
    tools = await setup_workspace

    # Create directory structure
    await tools.mkdir("/dir1")
    await tools.mkdir("/dir1/subdir")
    await tools.write(WriteRequest(path="/dir1/file.txt", content="test"))

    # Get tree
    tree_resp = await tools.tree("/")
    assert tree_resp.root.name == "."
    assert tree_resp.root.children is not None
    assert len(tree_resp.root.children) == 1
