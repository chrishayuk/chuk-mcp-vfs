"""
Basic usage example for chuk-mcp-vfs

This example demonstrates:
- Creating workspaces
- File operations
- Navigation
- Checkpoints
"""

import asyncio

from chuk_mcp_vfs.checkpoint_manager import CheckpointManager
from chuk_mcp_vfs.models import (
    CheckpointCreateRequest,
    ProviderType,
    WorkspaceCreateRequest,
    WriteRequest,
)
from chuk_mcp_vfs.vfs_tools import VFSTools
from chuk_mcp_vfs.workspace_manager import WorkspaceManager
from chuk_mcp_vfs.workspace_tools import WorkspaceTools


async def main():
    """Run basic usage demo."""

    # Initialize managers
    workspace_manager = WorkspaceManager()
    checkpoint_manager = CheckpointManager(workspace_manager)

    # Initialize tools
    workspace_tools = WorkspaceTools(workspace_manager)
    vfs_tools = VFSTools(workspace_manager)

    # Create a workspace
    print("Creating workspace...")
    create_req = WorkspaceCreateRequest(name="demo", provider=ProviderType.MEMORY)
    ws_info = await workspace_tools.workspace_create(create_req)
    print(f"Created workspace: {ws_info.name}")

    # Create directory structure
    print("\nCreating directories...")
    await vfs_tools.mkdir("/projects")
    await vfs_tools.mkdir("/projects/myapp")

    # Write files
    print("Writing files...")
    await vfs_tools.write(
        WriteRequest(
            path="/projects/myapp/main.py", content='print("Hello from VFS!")\n'
        )
    )
    await vfs_tools.write(
        WriteRequest(
            path="/projects/myapp/README.md", content="# My App\n\nA demo app.\n"
        )
    )

    # List directory
    print("\nListing /projects/myapp:")
    ls_resp = await vfs_tools.ls("/projects/myapp")
    for entry in ls_resp.entries:
        print(f"  {entry.type.value:10s} {entry.name}")

    # Read file
    print("\nReading main.py:")
    read_resp = await vfs_tools.read("/projects/myapp/main.py")
    print(read_resp.content)

    # Create checkpoint
    print("Creating checkpoint...")
    checkpoint_req = CheckpointCreateRequest(
        name="initial", description="Initial project structure"
    )
    checkpoint = await checkpoint_manager.create_checkpoint(
        name=checkpoint_req.name, description=checkpoint_req.description
    )
    print(f"Created checkpoint: {checkpoint.id}")

    # Modify files
    print("\nModifying files...")
    await vfs_tools.write(
        WriteRequest(
            path="/projects/myapp/main.py",
            content='print("Modified version!")\n',
        )
    )

    # Show modified content
    print("Modified main.py:")
    read_resp = await vfs_tools.read("/projects/myapp/main.py")
    print(read_resp.content)

    # Restore checkpoint
    print("Restoring checkpoint...")
    await checkpoint_manager.restore_checkpoint(checkpoint.id)

    # Show restored content
    print("Restored main.py:")
    read_resp = await vfs_tools.read("/projects/myapp/main.py")
    print(read_resp.content)

    # Show tree
    print("\nDirectory tree:")
    tree_resp = await vfs_tools.tree("/")
    print_tree(tree_resp.root, indent=0)

    print("\nDemo complete!")


def print_tree(node, indent=0):
    """Helper to print tree structure."""
    prefix = "  " * indent
    symbol = "📁" if node.type.value == "directory" else "📄"
    print(f"{prefix}{symbol} {node.name}")
    if node.children:
        for child in node.children:
            print_tree(child, indent + 1)


if __name__ == "__main__":
    asyncio.run(main())
