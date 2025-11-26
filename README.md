# chuk-mcp-vfs

**MCP server providing virtual filesystem workspaces via the unified namespace architecture.**

## Features

✅ **Unified Architecture** - Built on chuk-artifacts namespace system
✅ **Context-Aware** - Automatic user/session scoping from MCP context
✅ **Storage Scopes** - SESSION (ephemeral), USER (persistent), SANDBOX (shared)
✅ **Pydantic Native** - All requests and responses use Pydantic models
✅ **Async Native** - Fully async/await throughout
✅ **Type Safe** - Enums and constants instead of magic strings
✅ **Multiple Workspaces** - Create and manage isolated virtual filesystems
✅ **Full VFS Operations** - read, write, ls, tree, mkdir, rm, mv, cp, cd, pwd, find, grep
✅ **Checkpoints** - Save and restore filesystem state at any point
✅ **MCP Integration** - Expose all operations as MCP tools for AI agents

## Architecture

```
chuk-mcp-vfs           → Workspace management + VFS tools
    ↓ uses
chuk-artifacts         → Unified namespace architecture
    ↓ manages
Namespaces (WORKSPACE) → Each workspace is a namespace
    ↓ provides
chuk-virtual-fs        → Async VFS with multiple storage providers
    ↓
Storage Provider       → memory, filesystem, sqlite, s3
```

**Key Concepts:**
- **Everything is VFS**: Both blobs and workspaces are VFS-backed via namespaces
- **Scopes**: SESSION (per-conversation), USER (per-user persistent), SANDBOX (shared)
- **Context-Aware**: user_id and session_id automatically from MCP server context
- **Grid Architecture**: All namespaces stored in unified grid structure

## Installation

```bash
# Basic installation
pip install chuk-mcp-vfs

# With FUSE mounting support (Linux/macOS)
pip install chuk-mcp-vfs[mount]

# Development
pip install -e .[dev]
```

## Quick Start

### As MCP Server

```python
from chuk_mcp_vfs import run_server

# Start MCP server (stdio mode for Claude Desktop)
run_server()
```

### Programmatic Usage

```python
import asyncio
from chuk_mcp_vfs import (
    WorkspaceManager,
    ProviderType,
    StorageScope,
    WriteRequest,
)
from chuk_mcp_vfs.vfs_tools import VFSTools

async def main():
    # Initialize manager (uses chuk-artifacts under the hood)
    workspace_manager = WorkspaceManager()
    tools = VFSTools(workspace_manager)

    # Create SESSION-scoped workspace (ephemeral, tied to session)
    await workspace_manager.create_workspace(
        name="my-workspace",
        provider_type=ProviderType.MEMORY,
        scope=StorageScope.SESSION,  # or USER for persistence
    )

    # Write file
    await tools.write(WriteRequest(
        path="/hello.txt",
        content="Hello from VFS!"
    ))

    # Read file
    result = await tools.read("/hello.txt")
    print(result.content)

asyncio.run(main())
```

## MCP Tools

### Workspace Management

| Tool | Description |
|------|-------------|
| `workspace_create` | Create new workspace with provider (memory, filesystem, sqlite, s3) |
| `workspace_destroy` | Delete workspace and clean up resources |
| `workspace_list` | List all workspaces |
| `workspace_switch` | Switch active workspace |
| `workspace_info` | Get workspace details |
| `workspace_mount` | Mount workspace via FUSE (planned) |
| `workspace_unmount` | Unmount workspace (planned) |

### File Operations

| Tool | Description |
|------|-------------|
| `read` | Read file contents |
| `write` | Write file with content |
| `ls` | List directory contents |
| `tree` | Show directory tree structure |
| `mkdir` | Create directory |
| `rm` | Remove file/directory (with recursive option) |
| `mv` | Move/rename file/directory |
| `cp` | Copy file/directory (with recursive option) |

### Navigation

| Tool | Description |
|------|-------------|
| `cd` | Change current working directory |
| `pwd` | Print working directory |
| `find` | Find files by glob pattern |
| `grep` | Search file contents |

### Checkpoints

| Tool | Description |
|------|-------------|
| `checkpoint_create` | Create checkpoint of current state |
| `checkpoint_restore` | Restore from checkpoint |
| `checkpoint_list` | List all checkpoints |
| `checkpoint_delete` | Delete checkpoint |

## Usage with Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vfs": {
      "command": "chuk-mcp-vfs",
      "args": []
    }
  }
}
```

Then you can use natural language to interact with the filesystem:

```
You: Create a workspace called "myproject" and set up a Python project structure

Claude: [Uses workspace_create and mkdir tools]

You: Write a simple Flask app to main.py

Claude: [Uses write tool with Python code]

You: Create a checkpoint called "initial-setup"

Claude: [Uses checkpoint_create]

You: Make changes... actually restore to the checkpoint

Claude: [Uses checkpoint_restore]
```

## Examples

See `examples/basic_usage.py` for a complete working example.

## Storage Scopes

The unified architecture provides three storage scopes:

### SESSION Scope (Ephemeral)
```python
from chuk_mcp_vfs.models import StorageScope

# Create session-scoped workspace (default)
await workspace_manager.create_workspace(
    name="temp-work",
    scope=StorageScope.SESSION,  # Tied to current session
)
```
- **Lifetime**: Expires when session ends
- **Perfect for**: Temporary workspaces, caches, current work
- **Grid path**: `grid/{sandbox}/sess-{session_id}/{namespace_id}`
- **Access**: Only accessible from same session

### USER Scope (Persistent)
```python
# Create user-scoped workspace
await workspace_manager.create_workspace(
    name="my-project",
    scope=StorageScope.USER,  # Persists across sessions
)
```
- **Lifetime**: Persists across sessions
- **Perfect for**: User projects, personal data
- **Grid path**: `grid/{sandbox}/user-{user_id}/{namespace_id}`
- **Access**: Accessible from any session for the same user

### SANDBOX Scope (Shared)
```python
# Create sandbox-scoped workspace
await workspace_manager.create_workspace(
    name="shared-templates",
    scope=StorageScope.SANDBOX,  # Shared across all users
)
```
- **Lifetime**: Persists indefinitely
- **Perfect for**: Templates, shared docs, libraries
- **Grid path**: `grid/{sandbox}/shared/{namespace_id}`
- **Access**: Accessible by all users

## Provider Types

```python
from chuk_mcp_vfs.models import ProviderType

# In-memory (fast, temporary)
ProviderType.MEMORY

# Filesystem (persistent)
ProviderType.FILESYSTEM

# SQLite (portable database)
ProviderType.SQLITE

# S3 (cloud storage)
ProviderType.S3
```

## Models (Pydantic)

All requests and responses are Pydantic models:

```python
from chuk_mcp_vfs.models import (
    # Workspace models
    WorkspaceCreateRequest,
    WorkspaceCreateResponse,
    WorkspaceInfo,

    # File operation models
    WriteRequest,
    WriteResponse,
    ReadResponse,
    ListDirectoryResponse,

    # Navigation models
    FindRequest,
    FindResponse,
    GrepRequest,
    GrepResponse,

    # Checkpoint models
    CheckpointCreateRequest,
    CheckpointCreateResponse,
    CheckpointInfo,
)
```

## Development

```bash
# Install with dev dependencies
pip install -e .[dev]

# Run tests
pytest

# Run tests with coverage
pytest --cov=chuk_mcp_vfs

# Type checking
mypy src

# Linting
ruff check src
ruff format src
```

## Architecture Details

### Workspace Manager
- Thin wrapper around chuk-artifacts ArtifactStore
- Each workspace is a WORKSPACE-type namespace
- Tracks current working directory per workspace
- Context-aware: automatically uses user_id/session_id from MCP context
- Thread-safe workspace operations

### Namespace Integration
- All workspaces stored in unified grid architecture
- Automatic scope-based isolation (SESSION/USER/SANDBOX)
- Namespaces provide VFS instances via `get_namespace_vfs()`
- Grid paths make ownership and scope explicit

### Checkpoint Manager
- Wraps `chuk-virtual-fs` AsyncSnapshotManager
- Provides workspace-scoped checkpoints
- Metadata tracking for each checkpoint

### VFS Tools
- Wraps async VFS operations with Pydantic models
- Path resolution relative to current working directory
- Error handling and validation

### MCP Integration
- Registers all tools with `chuk-mcp-server`
- Automatic JSON schema generation from Pydantic models
- Context variables for user/session tracking
- Stdio transport for Claude Desktop

## Roadmap

- [x] Core VFS operations
- [x] Workspace management
- [x] Checkpoint system
- [x] Pydantic models
- [x] Basic tests
- [ ] FUSE mounting implementation
- [ ] Template system integration
- [ ] Workspace import/export
- [ ] File watching
- [ ] Permissions system
- [ ] Comprehensive tests

## License

MIT - see LICENSE file

## Contributing

Contributions welcome! Please ensure:
- All code uses Pydantic models (no dict returns)
- All code is async native
- Use enums/constants instead of magic strings
- Add tests for new features
- Update documentation

## Credits

Built on top of:
- [chuk-artifacts](https://github.com/chrishayuk/chuk-artifacts) - Unified namespace architecture
- [chuk-virtual-fs](https://github.com/chrishayuk/chuk-virtual-fs) - Virtual filesystem engine
- [chuk-mcp-server](https://github.com/chrishayuk/chuk-mcp-server) - MCP framework with context management
