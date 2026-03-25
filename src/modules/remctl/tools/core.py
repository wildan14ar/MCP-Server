"""
Core Utilities
Core SSH command execution utilities with session support.

Priority:
1. Use active session (from WebSocket) if available
2. Fall back to config-based execution
"""

from typing import Optional, List
from mcp.server.fastmcp import FastMCP
from ..config.session import RemctlSession
from ..config.tools import tool


@tool(name="server_exec")
async def execute_ssh_command(
    host: str,
    user: str,
    command: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    wait: float = 0.5,
) -> dict:
    """Execute a command on remote server via SSH."""
    # Create new SSH session
    ssh_session = RemctlSession(
        host=host,
        user=user,
        password=password,
        pkey_str=pkey_str,
        port=port,
    )

    try:
        ssh_session.connect()
        result = ssh_session.execute(command, wait=wait)
        ssh_session.close()

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


@tool(name="server_test_connection")
async def test_ssh_connection(
    host: str,
    user: str,
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
) -> dict:
    """Test SSH connection to remote server."""
    config, session = require_config_or_session()
    
    # If we have active session, connection is already working
    if session and session.is_active:
        return {
            "status": "success",
            "message": "Using active session",
            "session_id": session.session_id,
            "host": session.host,
            "user": session.user,
            "port": 22,
            "from_session": True
        }
    
    # Test new connection
    ssh_session = SSHSession(
        host=host or config.host,
        user=user or config.user,
        password=password or config.password,
        pkey_str=pkey_str or config.pkey_str,
        port=port or config.port,
    )

    try:
        ssh_session.connect()
        session_id = ssh_session.session_id
        ssh_session.close()

        return {
            "status": "success",
            "message": "Connection successful",
            "session_id": session_id,
            "host": host or config.host,
            "user": user or config.user,
            "port": port or config.port,
            "from_session": False
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection failed: {str(e)}",
            "session_id": "",
            "host": host or config.host,
            "user": user or config.user,
            "port": port or config.port,
            "from_session": False
        }


@tool(name="server_exec_multi")
async def execute_multiple_commands(
    host: str,
    user: str,
    commands: List[str],
    password: Optional[str] = None,
    pkey_str: Optional[str] = None,
    port: int = 22,
    wait: float = 0.5,
) -> dict:
    """Execute multiple commands in the same SSH session."""
    # Check for active session first
    session = get_session()
    if session and session.is_active:
        # Use shared session (WebSocket session)
        results = []
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
            except Exception as e:
                results.append({
                    "command": command,
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": 1,
                    "index": i,
                    "status": "error"
                })

        return {
            "status": "success",
            "session_id": session.session_id,
            "total_commands": len(commands),
            "results": results,
            "from_session": True
        }
    
    # Fallback: create new connection
    config, _ = require_config_or_session()
    ssh_session = SSHSession(
        host=host or config.host,
        user=user or config.user,
        password=password or config.password,
        pkey_str=pkey_str or config.pkey_str,
        port=port or config.port,
    )

    results = []

    try:
        ssh_session.connect()

        for i, command in enumerate(commands):
            try:
                result = ssh_session.execute(command, wait=wait)
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

        ssh_session.close()

        return {
            "status": "success",
            "session_id": ssh_session.session_id,
            "total_commands": len(commands),
            "results": results,
            "from_session": False
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "session_id": "",
            "total_commands": len(commands),
            "results": results,
            "from_session": False
        }
