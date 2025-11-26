"""
chuk-mcp-vfs - MCP server for virtual filesystem workspaces

Provides virtual filesystem operations, workspace management,
checkpoints, and optional FUSE mounting via MCP protocol.
"""

from chuk_mcp_vfs.checkpoint_manager import CheckpointManager
from chuk_mcp_vfs.models import (
    CheckpointCreateRequest,
    CheckpointInfo,
    CheckpointRestoreRequest,
    ProviderType,
    StorageScope,
    WorkspaceCreateRequest,
    WorkspaceInfo,
)
from chuk_mcp_vfs.server import create_server, main, run_server
from chuk_mcp_vfs.workspace_manager import WorkspaceManager

__version__ = "0.1.0"

__all__ = [
    # Main entry points
    "run_server",
    "create_server",
    "main",
    # Managers
    "WorkspaceManager",
    "CheckpointManager",
    # Models
    "ProviderType",
    "StorageScope",
    "WorkspaceInfo",
    "WorkspaceCreateRequest",
    "CheckpointInfo",
    "CheckpointCreateRequest",
    "CheckpointRestoreRequest",
]
