"""
MCP Server for chuk-mcp-vfs

Registers all VFS tools with the MCP framework.
"""

import sys

from chuk_mcp_server import ChukMCPServer

from chuk_mcp_vfs.checkpoint_manager import CheckpointManager
from chuk_mcp_vfs.checkpoint_tools import CheckpointTools
from chuk_mcp_vfs.models import (
    CheckpointCreateRequest,
    CheckpointRestoreRequest,
    CopyRequest,
    FindRequest,
    GrepRequest,
    WorkspaceCreateRequest,
    WorkspaceMountRequest,
    WriteRequest,
)
from chuk_mcp_vfs.vfs_tools import VFSTools
from chuk_mcp_vfs.workspace_manager import WorkspaceManager
from chuk_mcp_vfs.workspace_tools import WorkspaceTools


def create_server() -> ChukMCPServer:
    """Create and configure the MCP server with all VFS tools."""

    # Initialize managers
    workspace_manager = WorkspaceManager()
    checkpoint_manager = CheckpointManager(workspace_manager)

    # Initialize tool collections
    workspace_tools = WorkspaceTools(workspace_manager)
    vfs_tools = VFSTools(workspace_manager)
    checkpoint_tools_instance = CheckpointTools(checkpoint_manager)

    # Create MCP server
    server = ChukMCPServer()

    # ========================================================================
    # Register Workspace Tools
    # ========================================================================

    @server.tool
    async def workspace_create(request: WorkspaceCreateRequest):
        """Create a new virtual filesystem workspace."""
        return await workspace_tools.workspace_create(request)

    @server.tool
    async def workspace_destroy(name: str):
        """Destroy a workspace and clean up all resources."""
        return await workspace_tools.workspace_destroy(name)

    @server.tool
    async def workspace_list():
        """List all workspaces."""
        return await workspace_tools.workspace_list()

    @server.tool
    async def workspace_switch(name: str):
        """Switch to a different workspace."""
        return await workspace_tools.workspace_switch(name)

    @server.tool
    async def workspace_info(name: str | None = None):
        """Get detailed information about a workspace."""
        return await workspace_tools.workspace_info(name)

    @server.tool
    async def workspace_mount(request: WorkspaceMountRequest):
        """Mount workspace via FUSE."""
        return await workspace_tools.workspace_mount(request)

    @server.tool
    async def workspace_unmount(name: str | None = None):
        """Unmount workspace."""
        return await workspace_tools.workspace_unmount(name)

    # ========================================================================
    # Register File Operation Tools
    # ========================================================================

    @server.tool
    async def read(path: str):
        """Read file contents."""
        return await vfs_tools.read(path)

    @server.tool
    async def write(request: WriteRequest):
        """Write content to file."""
        return await vfs_tools.write(request)

    @server.tool
    async def ls(path: str = "."):
        """List directory contents."""
        return await vfs_tools.ls(path)

    @server.tool
    async def tree(path: str = ".", max_depth: int = 3):
        """Display directory tree structure."""
        return await vfs_tools.tree(path, max_depth)

    @server.tool
    async def mkdir(path: str):
        """Create directory."""
        return await vfs_tools.mkdir(path)

    @server.tool
    async def rm(path: str, recursive: bool = False):
        """Remove file or directory."""
        return await vfs_tools.rm(path, recursive)

    @server.tool
    async def mv(source: str, dest: str):
        """Move/rename file or directory."""
        return await vfs_tools.mv(source, dest)

    @server.tool
    async def cp(request: CopyRequest):
        """Copy file or directory."""
        return await vfs_tools.cp(request)

    # ========================================================================
    # Register Navigation Tools
    # ========================================================================

    @server.tool
    async def cd(path: str):
        """Change current working directory."""
        return await vfs_tools.cd(path)

    @server.tool
    async def pwd():
        """Get current working directory."""
        return await vfs_tools.pwd()

    @server.tool
    async def find(request: FindRequest):
        """Find files matching a pattern."""
        return await vfs_tools.find(request)

    @server.tool
    async def grep(request: GrepRequest):
        """Search file contents for a pattern."""
        return await vfs_tools.grep(request)

    # ========================================================================
    # Register Checkpoint Tools
    # ========================================================================

    @server.tool
    async def checkpoint_create(request: CheckpointCreateRequest):
        """Create a checkpoint of the current workspace state."""
        return await checkpoint_tools_instance.checkpoint_create(request)

    @server.tool
    async def checkpoint_restore(request: CheckpointRestoreRequest):
        """Restore workspace to a checkpoint."""
        return await checkpoint_tools_instance.checkpoint_restore(request)

    @server.tool
    async def checkpoint_list():
        """List all checkpoints for the current workspace."""
        return await checkpoint_tools_instance.checkpoint_list()

    @server.tool
    async def checkpoint_delete(checkpoint_id: str):
        """Delete a checkpoint."""
        return await checkpoint_tools_instance.checkpoint_delete(checkpoint_id)

    return server


def run_server() -> None:
    """Run the MCP server."""
    server = create_server()
    server.run_stdio()


def main() -> None:
    """Main entry point."""
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
