"""
Filesystem Tools - Remote file and directory operations.

Provides tools for:
- Directory navigation (ls, cd, pwd)
- File operations (cat, head, tail, file_info)
- File management (mkdir, rm, cp, mv)
- File search (find, grep)

NOTE: All tools require user approval before execution.
"""

from typing import Optional, List, Dict, Any
from ..config.session import RemctlSession
from ..config.tools import tool
from src.lib.gatekeeper import gatekeeper


@tool(name="server_ls")
async def list_directory(
    session_id: str,
    path: str = ".",
    long_format: bool = True,
    show_hidden: bool = False,
) -> dict:
    """
    List directory contents.

    Requires user approval before execution.

    Args:
        session_id: Session ID from WebSocket connection
        path: Directory path (default: current directory)
        long_format: Show detailed info (default: True)
        show_hidden: Show hidden files (default: False)

    Returns:
        Directory listing output
    """
    # Build command
    cmd = "ls"
    if long_format:
        cmd += " -l"
    if show_hidden:
        cmd += " -a"
    if path:
        cmd += f" {path}"

    # Create approval request
    request = gatekeeper.create_request("server_ls", {"session_id": session_id, "command": cmd})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    # Execute
    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_pwd")
async def print_working_directory(session_id: str) -> dict:
    """
    Print current working directory.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_pwd", {"session_id": session_id})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, "pwd")
    return result


@tool(name="server_cd")
async def change_directory(
    session_id: str,
    path: str,
) -> dict:
    """
    Change current directory.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_cd", {"session_id": session_id, "path": path})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, f"cd {path} && pwd")
    return result


@tool(name="server_mkdir")
async def make_directory(
    session_id: str,
    path: str,
    parents: bool = True,
) -> dict:
    """
    Create a directory.

    Requires user approval before execution.
    """
    cmd = "mkdir"
    if parents:
        cmd += " -p"
    cmd += f" {path}"

    request = gatekeeper.create_request("server_mkdir", {"session_id": session_id, "path": path})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_rm")
async def remove_file_or_dir(
    session_id: str,
    path: str,
    recursive: bool = False,
    force: bool = False,
) -> dict:
    """
    Remove a file or directory.

    ⚠️ WARNING: This will permanently delete the file/directory!
    Requires user approval before execution.
    """
    cmd = "rm"
    if recursive:
        cmd += " -r"
    if force:
        cmd += " -f"
    cmd += f" {path}"

    request = gatekeeper.create_request("server_rm", {"session_id": session_id, "path": path, "recursive": recursive})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_cp")
async def copy_file_or_dir(
    session_id: str,
    source: str,
    destination: str,
    recursive: bool = False,
) -> dict:
    """
    Copy a file or directory.

    Requires user approval before execution.
    """
    cmd = "cp"
    if recursive:
        cmd += " -r"
    cmd += f" {source} {destination}"

    request = gatekeeper.create_request("server_cp", {"session_id": session_id, "source": source, "destination": destination})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_mv")
async def move_or_rename(
    session_id: str,
    source: str,
    destination: str,
) -> dict:
    """
    Move or rename a file/directory.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_mv", {"session_id": session_id, "source": source, "destination": destination})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, f"mv {source} {destination}")
    return result


@tool(name="server_cat")
async def read_file_content(
    session_id: str,
    path: str,
    line_numbers: bool = False,
) -> dict:
    """
    Read and display file content.

    Requires user approval before execution.
    """
    cmd = "cat"
    if line_numbers:
        cmd += " -n"
    cmd += f" {path}"

    request = gatekeeper.create_request("server_cat", {"session_id": session_id, "path": path})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_head")
async def read_file_head(
    session_id: str,
    path: str,
    lines: int = 10,
) -> dict:
    """
    Read the first N lines of a file.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_head", {"session_id": session_id, "path": path, "lines": lines})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, f"head -n {lines} {path}")
    return result


@tool(name="server_tail")
async def read_file_tail(
    session_id: str,
    path: str,
    lines: int = 10,
    follow: bool = False,
) -> dict:
    """
    Read the last N lines of a file.

    Requires user approval before execution.
    """
    cmd = f"tail -n {lines}"
    if follow:
        cmd += " -f"
    cmd += f" {path}"

    request = gatekeeper.create_request("server_tail", {"session_id": session_id, "path": path, "lines": lines})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_file_info")
async def get_file_info(
    session_id: str,
    path: str,
) -> dict:
    """
    Get detailed file information (permissions, size, owner, etc.).

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_file_info", {"session_id": session_id, "path": path})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, f"stat {path}")
    return result


@tool(name="server_find")
async def find_files(
    session_id: str,
    path: str = ".",
    name_pattern: Optional[str] = None,
    file_type: Optional[str] = None,
    max_depth: Optional[int] = None,
) -> dict:
    """
    Search for files by name or type.

    Requires user approval before execution.

    Args:
        session_id: Session ID
        path: Starting directory
        name_pattern: Filename pattern (e.g., "*.log")
        file_type: File type filter (f=file, d=directory)
        max_depth: Maximum search depth
    """
    cmd = f"find {path}"

    if max_depth:
        cmd += f" -maxdepth {max_depth}"
    if file_type:
        cmd += f" -type {file_type}"
    if name_pattern:
        cmd += f" -name '{name_pattern}'"

    request = gatekeeper.create_request("server_find", {
        "session_id": session_id,
        "path": path,
        "name_pattern": name_pattern,
        "file_type": file_type
    })

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_grep")
async def grep_in_files(
    session_id: str,
    pattern: str,
    path: str = ".",
    recursive: bool = True,
    ignore_case: bool = True,
    line_numbers: bool = True,
    max_results: int = 50,
) -> dict:
    """
    Search for text pattern in files.

    Requires user approval before execution.
    """
    cmd = "grep"
    if recursive:
        cmd += " -r"
    if ignore_case:
        cmd += " -i"
    if line_numbers:
        cmd += " -n"
    cmd += f" '{pattern}' {path}"
    cmd += f" | head -n {max_results}"

    request = gatekeeper.create_request("server_grep", {
        "session_id": session_id,
        "pattern": pattern,
        "path": path,
        "recursive": recursive
    })

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result
