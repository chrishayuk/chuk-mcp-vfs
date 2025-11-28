"""
VFS Tools - MCP tools for virtual filesystem operations

All tools are async native and return Pydantic models.
"""

from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path

from chuk_mcp_vfs.models import (
    ChangeDirectoryResponse,
    CopyRequest,
    CopyResponse,
    FileEntry,
    FindRequest,
    FindResponse,
    GrepMatch,
    GrepRequest,
    GrepResponse,
    ListDirectoryResponse,
    MkdirResponse,
    MoveResponse,
    NodeType,
    PrintWorkingDirectoryResponse,
    ReadResponse,
    RemoveResponse,
    TreeNode,
    TreeResponse,
    WriteRequest,
    WriteResponse,
)
from chuk_mcp_vfs.workspace_manager import WorkspaceManager


class VFSTools:
    """Collection of VFS operation tools for MCP."""

    def __init__(self, workspace_manager: WorkspaceManager):
        self.workspace_manager = workspace_manager

    # ========================================================================
    # File Operations
    # ========================================================================

    async def read(self, path: str) -> ReadResponse:
        """
        Read file contents.

        Args:
            path: File path (absolute or relative to cwd)

        Returns:
            ReadResponse with file contents
        """
        vfs = self.workspace_manager.get_current_vfs()
        resolved_path = self.workspace_manager.resolve_path(path)

        content = await vfs.read_file(resolved_path)
        if content is None:
            raise ValueError(f"Could not read file: {resolved_path}")

        content_str = content.decode("utf-8") if isinstance(content, bytes) else content

        return ReadResponse(
            path=resolved_path, content=content_str, size=len(content_str.encode())
        )

    async def write(self, request: WriteRequest) -> WriteResponse:
        """
        Write content to file.

        Args:
            request: WriteRequest with path and content

        Returns:
            WriteResponse with success status
        """
        from pathlib import PurePosixPath

        vfs = self.workspace_manager.get_current_vfs()
        resolved_path = self.workspace_manager.resolve_path(request.path)

        # Ensure all parent directories exist
        # Use PurePosixPath to ensure forward slashes on all platforms
        parent = str(PurePosixPath(resolved_path).parent)
        if parent != "/":
            # Create all parent directories if they don't exist
            parts = [p for p in parent.split("/") if p]
            current_path = ""
            for part in parts:
                current_path += f"/{part}"
                if not await vfs.exists(current_path):
                    await vfs.mkdir(current_path)

        content_bytes = request.content.encode("utf-8")
        await vfs.write_file(resolved_path, content_bytes)

        return WriteResponse(success=True, path=resolved_path, size=len(content_bytes))

    async def ls(self, path: str = ".") -> ListDirectoryResponse:
        """
        List directory contents.

        Args:
            path: Directory path (default: current directory)

        Returns:
            ListDirectoryResponse with entries
        """
        vfs = self.workspace_manager.get_current_vfs()
        resolved_path = self.workspace_manager.resolve_path(path)

        # ls() returns list of filenames
        filenames = await vfs.ls(resolved_path)

        file_entries = []
        for name in filenames:
            # Construct full path
            if resolved_path == "/":
                full_path = f"/{name}"
            else:
                full_path = f"{resolved_path}/{name}"

            # Get node info for each entry
            node_info = await vfs.get_node_info(full_path)
            if node_info:
                # Parse modified_at timestamp if it's a string
                modified: datetime | None = None
                if node_info.modified_at:
                    if isinstance(node_info.modified_at, str):
                        modified = datetime.fromisoformat(node_info.modified_at)
                    else:
                        modified = node_info.modified_at

                file_entries.append(
                    FileEntry(
                        name=name,
                        path=full_path,
                        type=NodeType.DIRECTORY if node_info.is_dir else NodeType.FILE,
                        size=node_info.size,
                        modified=modified,
                    )
                )

        return ListDirectoryResponse(path=resolved_path, entries=file_entries)

    async def tree(self, path: str = ".", max_depth: int = 3) -> TreeResponse:
        """
        Display directory tree structure.

        Args:
            path: Root path for tree
            max_depth: Maximum depth to traverse

        Returns:
            TreeResponse with nested tree structure
        """
        vfs = self.workspace_manager.get_current_vfs()
        resolved_path = self.workspace_manager.resolve_path(path)

        async def build_tree(current_path: str, depth: int) -> TreeNode:
            if depth > max_depth:
                return TreeNode(name="...", type=NodeType.DIRECTORY, truncated=True)

            node_info = await vfs.get_node_info(current_path)
            if not node_info:
                return TreeNode(name="???", type=NodeType.FILE, size=0)

            node_type = NodeType.DIRECTORY if node_info.is_dir else NodeType.FILE

            if not node_info.is_dir:
                return TreeNode(
                    name=Path(current_path).name, type=node_type, size=node_info.size
                )

            # Recursively build tree for directory
            children: list[TreeNode] = []
            filenames = await vfs.ls(current_path)
            for name in filenames:
                if current_path == "/":
                    child_path = f"/{name}"
                else:
                    child_path = f"{current_path}/{name}"
                child_tree = await build_tree(child_path, depth + 1)
                children.append(child_tree)

            return TreeNode(
                name=Path(current_path).name if current_path != "/" else "/",
                type=node_type,
                children=children if children else None,
            )

        root = await build_tree(resolved_path, 0)
        return TreeResponse(root=root)

    async def mkdir(self, path: str) -> MkdirResponse:
        """
        Create directory.

        Args:
            path: Directory path to create

        Returns:
            MkdirResponse with success status
        """
        vfs = self.workspace_manager.get_current_vfs()
        resolved_path = self.workspace_manager.resolve_path(path)

        await vfs.mkdir(resolved_path)

        return MkdirResponse(success=True, path=resolved_path)

    async def rm(self, path: str, recursive: bool = False) -> RemoveResponse:
        """
        Remove file or directory.

        Args:
            path: Path to remove
            recursive: If True, remove directories recursively

        Returns:
            RemoveResponse with success status
        """
        vfs = self.workspace_manager.get_current_vfs()
        resolved_path = self.workspace_manager.resolve_path(path)

        node = await vfs.get_node_info(resolved_path)
        if not node:
            raise ValueError(f"Path not found: {resolved_path}")

        if node.is_dir and not recursive:
            raise ValueError(
                "Cannot remove directory without recursive=True. "
                "Use recursive=True to remove directories."
            )

        if node.is_dir:
            await vfs.rmdir(resolved_path)
        else:
            await vfs.rm(resolved_path)

        return RemoveResponse(success=True, path=resolved_path)

    async def mv(self, source: str, dest: str) -> MoveResponse:
        """
        Move/rename file or directory.

        Args:
            source: Source path
            dest: Destination path

        Returns:
            MoveResponse with success status
        """
        vfs = self.workspace_manager.get_current_vfs()
        resolved_source = self.workspace_manager.resolve_path(source)
        resolved_dest = self.workspace_manager.resolve_path(dest)

        await vfs.mv(resolved_source, resolved_dest)

        return MoveResponse(success=True, source=resolved_source, dest=resolved_dest)

    async def cp(self, request: CopyRequest) -> CopyResponse:
        """
        Copy file or directory.

        Args:
            request: CopyRequest with source, dest, and recursive flag

        Returns:
            CopyResponse with success status
        """
        vfs = self.workspace_manager.get_current_vfs()
        resolved_source = self.workspace_manager.resolve_path(request.source)
        resolved_dest = self.workspace_manager.resolve_path(request.dest)

        # Note: cp method doesn't have recursive parameter in AsyncVirtualFileSystem
        # It handles directories automatically
        await vfs.cp(resolved_source, resolved_dest)

        return CopyResponse(success=True, source=resolved_source, dest=resolved_dest)

    # ========================================================================
    # Navigation Operations
    # ========================================================================

    async def cd(self, path: str) -> ChangeDirectoryResponse:
        """
        Change current working directory.

        Args:
            path: Directory path

        Returns:
            ChangeDirectoryResponse with new cwd
        """
        vfs = self.workspace_manager.get_current_vfs()
        resolved_path = self.workspace_manager.resolve_path(path)

        # Verify path exists and is a directory
        node = await vfs.get_node_info(resolved_path)
        if not node or not node.is_dir:
            raise ValueError(f"Not a directory: {resolved_path}")

        self.workspace_manager.set_current_path(resolved_path)

        return ChangeDirectoryResponse(success=True, cwd=resolved_path)

    async def pwd(self) -> PrintWorkingDirectoryResponse:
        """
        Get current working directory.

        Returns:
            PrintWorkingDirectoryResponse with cwd
        """
        cwd = self.workspace_manager.get_current_path()
        return PrintWorkingDirectoryResponse(cwd=cwd)

    async def find(self, request: FindRequest) -> FindResponse:
        """
        Find files matching a pattern.

        Args:
            request: FindRequest with pattern, path, and max_results

        Returns:
            FindResponse with matching paths
        """
        vfs = self.workspace_manager.get_current_vfs()
        resolved_path = self.workspace_manager.resolve_path(request.path)

        results: list[str] = []
        truncated = False

        async def search(current_path: str) -> None:
            nonlocal truncated
            if len(results) >= request.max_results:
                truncated = True
                return

            filenames = await vfs.ls(current_path)
            for name in filenames:
                if len(results) >= request.max_results:
                    truncated = True
                    break

                # Construct full path
                if current_path == "/":
                    full_path = f"/{name}"
                else:
                    full_path = f"{current_path}/{name}"

                # Check if name matches pattern
                if fnmatch(name, request.pattern):
                    results.append(full_path)

                # Recurse into directories
                node_info = await vfs.get_node_info(full_path)
                if node_info and node_info.is_dir:
                    await search(full_path)

        await search(resolved_path)
        return FindResponse(
            pattern=request.pattern, matches=results, truncated=truncated
        )

    async def grep(self, request: GrepRequest) -> GrepResponse:
        """
        Search file contents for a pattern.

        Args:
            request: GrepRequest with pattern, path, and max_results

        Returns:
            GrepResponse with matches
        """
        vfs = self.workspace_manager.get_current_vfs()
        resolved_path = self.workspace_manager.resolve_path(request.path)

        matches: list[GrepMatch] = []
        truncated = False

        async def search_file(file_path: str) -> None:
            nonlocal truncated
            if len(matches) >= request.max_results:
                truncated = True
                return

            try:
                content = await vfs.read_file(file_path)
                if content is None:
                    return

                if isinstance(content, bytes):
                    content_str = content.decode("utf-8", errors="ignore")
                else:
                    content_str = content

                for line_num, line in enumerate(content_str.splitlines(), start=1):
                    if request.pattern in line:
                        matches.append(
                            GrepMatch(
                                file=file_path, line=line_num, content=line.strip()
                            )
                        )
                        if len(matches) >= request.max_results:
                            truncated = True
                            break
            except Exception:
                # Skip files that can't be read
                pass

        async def search_dir(current_path: str) -> None:
            nonlocal truncated
            if len(matches) >= request.max_results:
                truncated = True
                return

            filenames = await vfs.ls(current_path)
            for name in filenames:
                if len(matches) >= request.max_results:
                    truncated = True
                    break

                # Construct full path
                if current_path == "/":
                    full_path = f"/{name}"
                else:
                    full_path = f"{current_path}/{name}"

                node_info = await vfs.get_node_info(full_path)
                if not node_info:
                    continue

                if node_info.is_dir:
                    await search_dir(full_path)
                else:
                    await search_file(full_path)

        node = await vfs.get_node_info(resolved_path)
        if not node:
            raise ValueError(f"Path not found: {resolved_path}")

        if node.is_dir:
            await search_dir(resolved_path)
        else:
            await search_file(resolved_path)

        return GrepResponse(
            pattern=request.pattern, matches=matches, truncated=truncated
        )
