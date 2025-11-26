"""
Pydantic models for chuk-mcp-vfs
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

try:
    from chuk_artifacts import StorageScope
except ImportError:
    # Fallback if chuk-artifacts not installed
    class StorageScope(str, Enum):
        """Storage scope (fallback if chuk-artifacts not available)"""
        SESSION = "session"
        USER = "user"
        SANDBOX = "sandbox"


class ProviderType(str, Enum):
    """Storage provider types"""

    MEMORY = "memory"
    FILESYSTEM = "filesystem"
    SQLITE = "sqlite"
    S3 = "s3"


class NodeType(str, Enum):
    """Filesystem node types"""

    FILE = "file"
    DIRECTORY = "directory"


# ============================================================================
# Workspace Models
# ============================================================================


class WorkspaceInfo(BaseModel):
    """Information about a workspace"""

    name: str
    provider_type: ProviderType
    created_at: datetime
    current_path: str = "/"
    mount_point: str | None = None
    is_mounted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"use_enum_values": False}


class WorkspaceCreateRequest(BaseModel):
    """Request to create a workspace"""

    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    provider: ProviderType = ProviderType.MEMORY
    scope: StorageScope = StorageScope.SESSION
    template: str | None = None
    provider_config: dict[str, Any] = Field(default_factory=dict)


class WorkspaceCreateResponse(BaseModel):
    """Response from workspace creation"""

    name: str
    provider: ProviderType
    created_at: datetime
    current_path: str
    is_mounted: bool


class WorkspaceDestroyResponse(BaseModel):
    """Response from workspace destruction"""

    success: bool
    workspace: str


class WorkspaceListResponse(BaseModel):
    """Response from workspace list"""

    workspaces: list[WorkspaceInfo]


class WorkspaceSwitchResponse(BaseModel):
    """Response from workspace switch"""

    name: str
    provider: ProviderType
    current_path: str
    is_mounted: bool


class WorkspaceMountRequest(BaseModel):
    """Request to mount workspace"""

    name: str | None = None
    mount_point: str | None = None


class WorkspaceMountResponse(BaseModel):
    """Response from workspace mount"""

    success: bool
    workspace: str
    mount_point: str | None = None
    error: str | None = None


class WorkspaceUnmountResponse(BaseModel):
    """Response from workspace unmount"""

    success: bool
    workspace: str
    mount_point: str | None = None
    error: str | None = None


# ============================================================================
# File Operation Models
# ============================================================================


class FileEntry(BaseModel):
    """A file or directory entry"""

    name: str
    path: str
    type: NodeType
    size: int
    modified: datetime | None = None


class ReadResponse(BaseModel):
    """Response from read operation"""

    path: str
    content: str
    size: int


class WriteRequest(BaseModel):
    """Request to write a file"""

    path: str
    content: str


class WriteResponse(BaseModel):
    """Response from write operation"""

    success: bool
    path: str
    size: int


class ListDirectoryResponse(BaseModel):
    """Response from ls operation"""

    path: str
    entries: list[FileEntry]


class TreeNode(BaseModel):
    """Node in a directory tree"""

    name: str
    type: NodeType
    size: int | None = None
    children: list["TreeNode"] | None = None
    truncated: bool = False


class TreeResponse(BaseModel):
    """Response from tree operation"""

    root: TreeNode


class MkdirResponse(BaseModel):
    """Response from mkdir operation"""

    success: bool
    path: str


class RemoveResponse(BaseModel):
    """Response from rm operation"""

    success: bool
    path: str


class MoveResponse(BaseModel):
    """Response from mv operation"""

    success: bool
    source: str
    dest: str


class CopyRequest(BaseModel):
    """Request to copy file/directory"""

    source: str
    dest: str
    recursive: bool = False


class CopyResponse(BaseModel):
    """Response from cp operation"""

    success: bool
    source: str
    dest: str


# ============================================================================
# Navigation Models
# ============================================================================


class ChangeDirectoryResponse(BaseModel):
    """Response from cd operation"""

    success: bool
    cwd: str


class PrintWorkingDirectoryResponse(BaseModel):
    """Response from pwd operation"""

    cwd: str


class FindRequest(BaseModel):
    """Request to find files"""

    pattern: str
    path: str = "."
    max_results: int = Field(default=100, ge=1, le=1000)


class FindResponse(BaseModel):
    """Response from find operation"""

    pattern: str
    matches: list[str]
    truncated: bool = False


class GrepMatch(BaseModel):
    """A grep match result"""

    file: str
    line: int
    content: str


class GrepRequest(BaseModel):
    """Request to grep files"""

    pattern: str
    path: str = "."
    max_results: int = Field(default=100, ge=1, le=1000)


class GrepResponse(BaseModel):
    """Response from grep operation"""

    pattern: str
    matches: list[GrepMatch]
    truncated: bool = False


# ============================================================================
# Checkpoint Models
# ============================================================================


class CheckpointInfo(BaseModel):
    """Information about a checkpoint"""

    id: str
    name: str | None = None
    description: str
    created_at: datetime
    workspace: str
    provider_type: ProviderType
    stats: dict[str, Any] = Field(default_factory=dict)


class CheckpointCreateRequest(BaseModel):
    """Request to create checkpoint"""

    name: str | None = None
    description: str = ""


class CheckpointCreateResponse(BaseModel):
    """Response from checkpoint creation"""

    success: bool
    checkpoint_id: str
    created_at: datetime


class CheckpointRestoreRequest(BaseModel):
    """Request to restore checkpoint"""

    checkpoint_id: str


class CheckpointRestoreResponse(BaseModel):
    """Response from checkpoint restore"""

    success: bool
    checkpoint_id: str
    restored_at: datetime


class CheckpointListResponse(BaseModel):
    """Response from checkpoint list"""

    checkpoints: list[CheckpointInfo]


class CheckpointDiffRequest(BaseModel):
    """Request to diff checkpoints"""

    checkpoint_a: str
    checkpoint_b: str


class FileDiff(BaseModel):
    """Difference between two file states"""

    path: str
    status: str  # "added", "removed", "modified", "unchanged"
    size_before: int | None = None
    size_after: int | None = None


class CheckpointDiffResponse(BaseModel):
    """Response from checkpoint diff"""

    checkpoint_a: str
    checkpoint_b: str
    files: list[FileDiff]
    summary: dict[str, int]  # {"added": N, "removed": N, "modified": N}


# ============================================================================
# Template Models
# ============================================================================


class TemplateInfo(BaseModel):
    """Information about a template"""

    name: str
    description: str
    files: list[str]
    directories: list[str]


class TemplateListResponse(BaseModel):
    """Response from template list"""

    templates: list[TemplateInfo]
