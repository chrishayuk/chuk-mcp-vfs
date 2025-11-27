"""
Tests for VFS Tools
"""

import pytest

from chuk_mcp_vfs.models import (
    CopyRequest,
    FindRequest,
    GrepRequest,
    ProviderType,
    WriteRequest,
)
from chuk_mcp_vfs.vfs_tools import VFSTools
from chuk_mcp_vfs.workspace_manager import WorkspaceManager


@pytest.fixture
def setup_workspace():
    """Fixture to create a workspace for testing."""

    async def _setup():
        manager = WorkspaceManager()
        await manager.create_workspace(name="test", provider_type=ProviderType.MEMORY)
        tools = VFSTools(manager)
        return tools

    return _setup


@pytest.mark.asyncio
async def test_write_and_read(setup_workspace):
    """Test writing and reading a file."""
    tools = await setup_workspace()

    # Write file
    write_resp = await tools.write(
        WriteRequest(path="/test.txt", content="Hello World")
    )
    assert write_resp.success
    assert write_resp.path == "/test.txt"

    # Read file
    read_resp = await tools.read("/test.txt")
    assert read_resp.content == "Hello World"
    assert read_resp.path == "/test.txt"


@pytest.mark.asyncio
async def test_mkdir_and_ls(setup_workspace):
    """Test creating directory and listing."""
    tools = await setup_workspace()

    # Create directory
    mkdir_resp = await tools.mkdir("/testdir")
    assert mkdir_resp.success
    assert mkdir_resp.path == "/testdir"

    # List root
    ls_resp = await tools.ls("/")
    # Should have testdir and possibly .workspace
    assert len(ls_resp.entries) >= 1
    testdir_entries = [e for e in ls_resp.entries if e.name == "testdir"]
    assert len(testdir_entries) == 1
    assert testdir_entries[0].type.value == "directory"


@pytest.mark.asyncio
async def test_cd_and_pwd(setup_workspace):
    """Test changing directory and getting working directory."""
    tools = await setup_workspace()

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
    tools = await setup_workspace()

    # Create directory structure
    await tools.mkdir("/dir1")
    await tools.mkdir("/dir1/subdir")
    await tools.write(WriteRequest(path="/dir1/file.txt", content="test"))

    # Get tree
    tree_resp = await tools.tree("/")
    assert tree_resp.root.name == "/"
    assert tree_resp.root.children is not None
    assert len(tree_resp.root.children) >= 1


@pytest.mark.asyncio
async def test_rm_file(setup_workspace):
    """Test removing a file."""
    tools = await setup_workspace()

    # Create file
    await tools.write(WriteRequest(path="/remove_me.txt", content="delete this"))

    # Remove file
    rm_resp = await tools.rm("/remove_me.txt")
    assert rm_resp.success
    assert rm_resp.path == "/remove_me.txt"

    # Verify removed
    ls_resp = await tools.ls("/")
    filenames = [e.name for e in ls_resp.entries]
    assert "remove_me.txt" not in filenames


@pytest.mark.asyncio
async def test_rm_empty_directory(setup_workspace):
    """Test removing an empty directory."""
    tools = await setup_workspace()

    # Create empty directory
    await tools.mkdir("/remove_dir")

    # Remove directory recursively
    rm_resp = await tools.rm("/remove_dir", recursive=True)
    assert rm_resp.success


@pytest.mark.asyncio
async def test_mv(setup_workspace):
    """Test moving/renaming files."""
    tools = await setup_workspace()

    # Create file
    await tools.write(WriteRequest(path="/old_name.txt", content="move me"))

    # Move file
    mv_resp = await tools.mv("/old_name.txt", "/new_name.txt")
    assert mv_resp.success
    assert mv_resp.source == "/old_name.txt"
    assert mv_resp.dest == "/new_name.txt"

    # Verify moved
    ls_resp = await tools.ls("/")
    filenames = [e.name for e in ls_resp.entries]
    assert "old_name.txt" not in filenames
    assert "new_name.txt" in filenames


@pytest.mark.asyncio
async def test_cp(setup_workspace):
    """Test copying files."""
    tools = await setup_workspace()

    # Create file
    await tools.write(WriteRequest(path="/original.txt", content="copy me"))

    # Copy file
    cp_req = CopyRequest(source="/original.txt", dest="/copy.txt", recursive=False)
    cp_resp = await tools.cp(cp_req)
    assert cp_resp.success
    assert cp_resp.source == "/original.txt"
    assert cp_resp.dest == "/copy.txt"

    # Verify both exist
    ls_resp = await tools.ls("/")
    filenames = [e.name for e in ls_resp.entries]
    assert "original.txt" in filenames
    assert "copy.txt" in filenames


@pytest.mark.asyncio
async def test_find(setup_workspace):
    """Test finding files by pattern."""
    tools = await setup_workspace()

    # Create test files
    await tools.mkdir("/search")
    await tools.write(WriteRequest(path="/search/file1.txt", content="test"))
    await tools.write(WriteRequest(path="/search/file2.txt", content="test"))
    await tools.write(WriteRequest(path="/search/other.md", content="test"))

    # Find txt files
    find_req = FindRequest(pattern="*.txt", path="/search", max_results=100)
    find_resp = await tools.find(find_req)

    assert len(find_resp.matches) == 2
    assert "/search/file1.txt" in find_resp.matches
    assert "/search/file2.txt" in find_resp.matches
    assert not find_resp.truncated


@pytest.mark.asyncio
async def test_grep(setup_workspace):
    """Test searching file contents."""
    tools = await setup_workspace()

    # Create files with content
    await tools.mkdir("/grep_test")
    await tools.write(WriteRequest(path="/grep_test/file1.txt", content="hello world"))
    await tools.write(
        WriteRequest(path="/grep_test/file2.txt", content="foo bar\nhello there")
    )

    # Search for "hello"
    grep_req = GrepRequest(pattern="hello", path="/grep_test", max_results=100)
    grep_resp = await tools.grep(grep_req)

    assert len(grep_resp.matches) == 2
    files_matched = {m.file for m in grep_resp.matches}
    assert "/grep_test/file1.txt" in files_matched
    assert "/grep_test/file2.txt" in files_matched


@pytest.mark.asyncio
async def test_write_with_nested_path(setup_workspace):
    """Test writing to nested paths."""
    tools = await setup_workspace()

    # Create parent first
    await tools.mkdir("/deep")
    await tools.mkdir("/deep/nested")

    # Write to nested path
    write_resp = await tools.write(
        WriteRequest(path="/deep/nested/file.txt", content="test")
    )

    assert write_resp.success

    # Verify file exists
    read_resp = await tools.read("/deep/nested/file.txt")
    assert read_resp.content == "test"


@pytest.mark.asyncio
async def test_cd_invalid_directory(setup_workspace):
    """Test cd to invalid directory raises error."""
    tools = await setup_workspace()

    with pytest.raises(ValueError, match="Not a directory"):
        await tools.cd("/nonexistent")


@pytest.mark.asyncio
async def test_rm_nonexistent_path(setup_workspace):
    """Test removing non-existent path raises error."""
    tools = await setup_workspace()

    with pytest.raises(ValueError, match="Path not found"):
        await tools.rm("/nonexistent.txt")


@pytest.mark.asyncio
async def test_rm_directory_without_recursive(setup_workspace):
    """Test removing directory without recursive flag raises error."""
    tools = await setup_workspace()

    await tools.mkdir("/somedir")

    with pytest.raises(ValueError, match="Cannot remove directory"):
        await tools.rm("/somedir", recursive=False)


@pytest.mark.asyncio
async def test_ls_default_path(setup_workspace):
    """Test ls with default path (.)."""
    tools = await setup_workspace()

    # List current directory (defaults to /)
    ls_resp = await tools.ls()

    assert ls_resp.path == "/"
    assert isinstance(ls_resp.entries, list)


@pytest.mark.asyncio
async def test_tree_max_depth(setup_workspace):
    """Test tree with max depth limit."""
    tools = await setup_workspace()

    # Create deep structure
    await tools.mkdir("/a")
    await tools.mkdir("/a/b")
    await tools.mkdir("/a/b/c")
    await tools.mkdir("/a/b/c/d")

    # Get tree with depth limit
    tree_resp = await tools.tree("/", max_depth=2)

    assert tree_resp.root.name == "/"
    assert tree_resp.root.children is not None


@pytest.mark.asyncio
async def test_find_truncated(setup_workspace):
    """Test find with result truncation."""
    tools = await setup_workspace()

    # Create many files
    await tools.mkdir("/many")
    for i in range(10):
        await tools.write(WriteRequest(path=f"/many/file{i}.txt", content=f"file {i}"))

    # Find with small max_results
    find_req = FindRequest(pattern="*.txt", path="/many", max_results=5)
    find_resp = await tools.find(find_req)

    assert len(find_resp.matches) == 5
    assert find_resp.truncated is True


@pytest.mark.asyncio
async def test_grep_truncated(setup_workspace):
    """Test grep with result truncation."""
    tools = await setup_workspace()

    # Create files with pattern
    await tools.mkdir("/greptest")
    for i in range(10):
        await tools.write(
            WriteRequest(path=f"/greptest/file{i}.txt", content=f"match pattern {i}")
        )

    # Grep with small max_results
    grep_req = GrepRequest(pattern="pattern", path="/greptest", max_results=5)
    grep_resp = await tools.grep(grep_req)

    assert len(grep_resp.matches) == 5
    assert grep_resp.truncated is True


@pytest.mark.asyncio
async def test_grep_single_file(setup_workspace):
    """Test grep on a single file."""
    tools = await setup_workspace()

    await tools.write(
        WriteRequest(path="/single.txt", content="line 1\nline 2\nline 3")
    )

    grep_req = GrepRequest(pattern="line", path="/single.txt", max_results=100)
    grep_resp = await tools.grep(grep_req)

    assert len(grep_resp.matches) == 3


@pytest.mark.asyncio
async def test_grep_nonexistent_path(setup_workspace):
    """Test grep on non-existent path raises error."""
    tools = await setup_workspace()

    grep_req = GrepRequest(pattern="test", path="/nonexistent", max_results=100)

    with pytest.raises(ValueError, match="Path not found"):
        await tools.grep(grep_req)


@pytest.mark.asyncio
async def test_cd_to_file(setup_workspace):
    """Test cd to a file raises error."""
    tools = await setup_workspace()

    await tools.write(WriteRequest(path="/file.txt", content="test"))

    with pytest.raises(ValueError, match="Not a directory"):
        await tools.cd("/file.txt")


@pytest.mark.asyncio
async def test_ls_with_empty_entries(setup_workspace):
    """Test ls on empty directory."""
    tools = await setup_workspace()

    await tools.mkdir("/empty")

    ls_resp = await tools.ls("/empty")

    assert ls_resp.path == "/empty"
    assert len(ls_resp.entries) == 0


@pytest.mark.asyncio
async def test_write_creates_parent_directory(setup_workspace):
    """Test that write creates parent directory if it doesn't exist."""
    tools = await setup_workspace()

    # Write to nested path without creating parents first
    write_resp = await tools.write(
        WriteRequest(path="/auto/created/file.txt", content="test content")
    )

    assert write_resp.success
    assert write_resp.path == "/auto/created/file.txt"

    # Verify we can read it back
    read_resp = await tools.read("/auto/created/file.txt")
    assert read_resp.content == "test content"


@pytest.mark.asyncio
async def test_read_nonexistent_file(setup_workspace):
    """Test reading non-existent file raises error."""
    tools = await setup_workspace()

    with pytest.raises(ValueError, match="Could not read file"):
        await tools.read("/nonexistent.txt")
