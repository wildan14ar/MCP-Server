"""
Terminal MCP Tools
Provides SSH command execution and terminal management
"""

from typing import Optional, List, Dict, Any
from src.terminal.ssh_session import SSHSession


# ============ BASIC INFO TOOLS ============

async def whoami(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
) -> dict:
    """
    Get current user information.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
    
    Returns:
        dict with username and user info
    """
    return await execute_ssh_command(
        host=host,
        user=user,
        command="whoami",
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.3
    )


async def pwd(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
) -> dict:
    """
    Get current working directory.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
    
    Returns:
        dict with current directory path
    """
    return await execute_ssh_command(
        host=host,
        user=user,
        command="pwd",
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.3
    )


async def hostname_info(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
) -> dict:
    """
    Get hostname information.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
    
    Returns:
        dict with hostname
    """
    return await execute_ssh_command(
        host=host,
        user=user,
        command="hostname",
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.3
    )


async def uname(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    flags: str = "-a",
) -> dict:
    """
    Get system information (uname).
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        flags: uname flags (default: -a for all info)
    
    Returns:
        dict with system information
    """
    return await execute_ssh_command(
        host=host,
        user=user,
        command=f"uname {flags}",
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.3
    )


# ============ FILE LISTING TOOLS ============

async def ls(
    host: str,
    user: str,
    path: str = ".",
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    long_format: bool = False,
    all_files: bool = False,
    human_readable: bool = False,
) -> dict:
    """
    List directory contents.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        path: Directory path to list (default: current directory)
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        long_format: Use long listing format (-l)
        all_files: Show hidden files (-a)
        human_readable: Human readable sizes (-h)
    
    Returns:
        dict with directory listing
    """
    flags = []
    if long_format:
        flags.append("-l")
    if all_files:
        flags.append("-a")
    if human_readable:
        flags.append("-h")
    
    flags_str = " ".join(flags)
    command = f"ls {flags_str} {path}".strip()
    
    return await execute_ssh_command(
        host=host,
        user=user,
        command=command,
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.5
    )


async def tree(
    host: str,
    user: str,
    path: str = ".",
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    max_depth: Optional[int] = None,
) -> dict:
    """
    Display directory tree structure.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        path: Directory path to display (default: current directory)
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        max_depth: Maximum depth to display (optional)
    
    Returns:
        dict with tree structure
    """
    command = f"tree {path}"
    if max_depth:
        command += f" -L {max_depth}"
    
    return await execute_ssh_command(
        host=host,
        user=user,
        command=command,
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=1.0
    )


# ============ FILE SEARCH TOOLS ============

async def find_files(
    host: str,
    user: str,
    path: str = ".",
    name_pattern: Optional[str] = None,
    file_type: Optional[str] = None,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    max_depth: Optional[int] = None,
) -> dict:
    """
    Find files matching criteria.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        path: Starting directory path (default: current directory)
        name_pattern: Filename pattern (e.g., "*.txt", "test*")
        file_type: File type (f=file, d=directory, l=symlink)
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        max_depth: Maximum depth to search (optional)
    
    Returns:
        dict with found files
    """
    command = f"find {path}"
    
    if max_depth:
        command += f" -maxdepth {max_depth}"
    
    if file_type:
        command += f" -type {file_type}"
    
    if name_pattern:
        command += f" -name '{name_pattern}'"
    
    return await execute_ssh_command(
        host=host,
        user=user,
        command=command,
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=2.0
    )


async def grep_files(
    host: str,
    user: str,
    pattern: str,
    path: str = ".",
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    recursive: bool = True,
    case_insensitive: bool = False,
    show_line_numbers: bool = True,
) -> dict:
    """
    Search for text pattern in files.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        pattern: Text pattern to search for
        path: Directory or file path to search
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        recursive: Search recursively (-r)
        case_insensitive: Case insensitive search (-i)
        show_line_numbers: Show line numbers (-n)
    
    Returns:
        dict with matching lines
    """
    flags = []
    if recursive:
        flags.append("-r")
    if case_insensitive:
        flags.append("-i")
    if show_line_numbers:
        flags.append("-n")
    
    flags_str = " ".join(flags)
    command = f"grep {flags_str} '{pattern}' {path}"
    
    return await execute_ssh_command(
        host=host,
        user=user,
        command=command,
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=2.0
    )


async def locate_file(
    host: str,
    user: str,
    pattern: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    limit: Optional[int] = None,
) -> dict:
    """
    Quickly locate files by name (uses locate database).
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        pattern: Filename pattern to locate
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        limit: Limit number of results (optional)
    
    Returns:
        dict with found file paths
    """
    command = f"locate '{pattern}'"
    if limit:
        command += f" | head -n {limit}"
    
    return await execute_ssh_command(
        host=host,
        user=user,
        command=command,
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=1.0
    )


# ============ FILE OPERATIONS TOOLS ============

async def cat_file(
    host: str,
    user: str,
    file_path: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    lines: Optional[int] = None,
) -> dict:
    """
    Display file contents.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        file_path: Path to file
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        lines: Limit to first N lines (optional)
    
    Returns:
        dict with file contents
    """
    command = f"cat {file_path}"
    if lines:
        command += f" | head -n {lines}"
    
    return await execute_ssh_command(
        host=host,
        user=user,
        command=command,
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=1.0
    )


async def tail_file(
    host: str,
    user: str,
    file_path: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    lines: int = 10,
) -> dict:
    """
    Display last N lines of file.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        file_path: Path to file
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        lines: Number of lines to show (default: 10)
    
    Returns:
        dict with file tail
    """
    return await execute_ssh_command(
        host=host,
        user=user,
        command=f"tail -n {lines} {file_path}",
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.5
    )


async def head_file(
    host: str,
    user: str,
    file_path: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    lines: int = 10,
) -> dict:
    """
    Display first N lines of file.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        file_path: Path to file
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        lines: Number of lines to show (default: 10)
    
    Returns:
        dict with file head
    """
    return await execute_ssh_command(
        host=host,
        user=user,
        command=f"head -n {lines} {file_path}",
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.5
    )


async def file_info(
    host: str,
    user: str,
    path: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
) -> dict:
    """
    Get detailed file/directory information.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        path: Path to file or directory
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
    
    Returns:
        dict with file info (size, permissions, timestamps)
    """
    return await execute_ssh_command(
        host=host,
        user=user,
        command=f"stat {path}",
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.5
    )


# ============ SYSTEM INFO TOOLS ============

async def disk_usage(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    human_readable: bool = True,
) -> dict:
    """
    Get disk usage information.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        human_readable: Human readable sizes (default: True)
    
    Returns:
        dict with disk usage info
    """
    command = "df -h" if human_readable else "df"
    
    return await execute_ssh_command(
        host=host,
        user=user,
        command=command,
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.5
    )


async def memory_usage(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    human_readable: bool = True,
) -> dict:
    """
    Get memory usage information.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        human_readable: Human readable sizes (default: True)
    
    Returns:
        dict with memory usage info
    """
    command = "free -h" if human_readable else "free"
    
    return await execute_ssh_command(
        host=host,
        user=user,
        command=command,
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.5
    )


async def process_list(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    user_filter: Optional[str] = None,
) -> dict:
    """
    List running processes.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        user_filter: Filter by username (optional)
    
    Returns:
        dict with process list
    """
    command = "ps aux"
    if user_filter:
        command += f" | grep {user_filter}"
    
    return await execute_ssh_command(
        host=host,
        user=user,
        command=command,
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=1.0
    )


async def uptime_info(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
) -> dict:
    """
    Get system uptime and load average.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
    
    Returns:
        dict with uptime info
    """
    return await execute_ssh_command(
        host=host,
        user=user,
        command="uptime",
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.3
    )


# ============ NETWORK TOOLS ============

async def network_interfaces(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
) -> dict:
    """
    Get network interface information.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
    
    Returns:
        dict with network interfaces info
    """
    return await execute_ssh_command(
        host=host,
        user=user,
        command="ip addr show || ifconfig",
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=0.5
    )


async def ping_host(
    host: str,
    user: str,
    target: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    count: int = 4,
) -> dict:
    """
    Ping a target host.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        target: Target host to ping
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        count: Number of ping packets (default: 4)
    
    Returns:
        dict with ping results
    """
    return await execute_ssh_command(
        host=host,
        user=user,
        command=f"ping -c {count} {target}",
        password=password,
        pkey_str=pkey_str,
        port=port,
        wait=count + 1
    )


# ============ HELPER FUNCTIONS ============

async def execute_ssh_command(
    host: str,
    user: str,
    command: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    wait: float = 0.5,
) -> dict:
    """
    Execute a command on remote server via SSH.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        command: Command to execute
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        wait: Time to wait for command output
    
    Returns:
        dict with stdout, stderr, returncode, and session_id
    """
    session = SSHSession(
        host=host,
        user=user,
        password=password,
        pkey_str=pkey_str,
        port=port,
    )
    
    try:
        session.connect()
        result = session.execute(command, wait=wait)
        session.close()
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "session_id": result.session_id,
            "status": "success"
        }
    except PermissionError as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": 1,
            "session_id": "",
            "status": "permission_denied"
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": 1,
            "session_id": "",
            "status": "error"
        }


async def test_ssh_connection(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
) -> dict:
    """
    Test SSH connection to remote server.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
    
    Returns:
        dict with connection status and info
    """
    session = SSHSession(
        host=host,
        user=user,
        password=password,
        pkey_str=pkey_str,
        port=port,
    )
    
    try:
        session.connect()
        session_id = session.session_id
        session.close()
        
        return {
            "status": "success",
            "message": "Connection successful",
            "session_id": session_id,
            "host": host,
            "user": user,
            "port": port
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection failed: {str(e)}",
            "session_id": "",
            "host": host,
            "user": user,
            "port": port
        }


async def execute_multiple_commands(
    host: str,
    user: str,
    commands: list[str],
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    wait: float = 0.5,
) -> dict:
    """
    Execute multiple commands in the same SSH session.
    
    Args:
        host: SSH server hostname or IP
        user: SSH username
        commands: List of commands to execute
        password: SSH password (optional)
        pkey_str: SSH private key as string (optional)
        port: SSH port (default 22)
        wait: Time to wait for each command output
    
    Returns:
        dict with results for each command
    """
    session = SSHSession(
        host=host,
        user=user,
        password=password,
        pkey_str=pkey_str,
        port=port,
    )
    
    results = []
    
    try:
        session.connect()
        
        for i, command in enumerate(commands):
            try:
                result = session.execute(command, wait=wait)
                results.append({
                    "command": command,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "index": i,
                    "status": "success"
                })
            except PermissionError as e:
                results.append({
                    "command": command,
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": 1,
                    "index": i,
                    "status": "permission_denied"
                })
            except Exception as e:
                results.append({
                    "command": command,
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": 1,
                    "index": i,
                    "status": "error"
                })
        
        session.close()
        
        return {
            "status": "success",
            "session_id": session.session_id,
            "total_commands": len(commands),
            "results": results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "session_id": "",
            "total_commands": len(commands),
            "results": results
        }
