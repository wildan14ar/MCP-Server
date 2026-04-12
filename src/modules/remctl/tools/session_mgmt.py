"""
Remctl Session Management - Create new SSH sessions via MCP.

AI can create NEW SSH sessions WITHOUT sending credentials.
Credentials come from the stored WS session credentials.

These tools DO NOT require user approval.
"""

from typing import Optional
from ..config.session import RemctlSession
from src.lib.gatekeeper import get_credentials


async def create_ssh_session(
    host: str,
    port: int = 22,
) -> dict:
    """
    Create a new SSH session using stored credentials.

    AI does NOT send credentials - they come from the user's WS session.

    Args:
        host: Target server hostname/IP
        port: SSH port (default: 22)

    Returns:
        New session ID
    """
    # Get stored credentials from WS session
    creds = get_credentials("remctl")
    if not creds:
        return {
            "status": "error",
            "message": "No stored credentials. User must connect via WebSocket first."
        }

    try:
        session_id = RemctlSession.create(
            host=host,
            user=creds["user"],
            password=creds.get("password"),
            pkey_str=creds.get("pkey_str"),
            port=port,
        )
        return {
            "status": "success",
            "session_id": session_id,
            "host": host,
            "user": creds["user"],
            "message": f"New SSH session created for {creds['user']}@{host}:{port}. Use session_id for commands."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def list_ssh_sessions() -> dict:
    """
    List all active SSH sessions.

    Returns:
        List of active sessions
    """
    sessions = RemctlSession.list()
    return {
        "status": "success",
        "sessions": sessions,
        "total": len(sessions)
    }


async def close_ssh_session(session_id: str) -> dict:
    """
    Close an SSH session.

    Args:
        session_id: Session ID from server_connect or server_new_session

    Returns:
        Status message
    """
    success = RemctlSession.close(session_id)
    if success:
        return {
            "status": "success",
            "session_id": session_id,
            "message": "SSH session closed"
        }
    return {
        "status": "error",
        "message": f"Session '{session_id}' not found"
    }


def register_session_tools(mcp):
    """Register session management tools manually (not via @tool decorator) so params are visible."""
    mcp.tool(name="server_new_session")(create_ssh_session)
    mcp.tool(name="server_list_sessions")(list_ssh_sessions)
    mcp.tool(name="server_close_session")(close_ssh_session)
