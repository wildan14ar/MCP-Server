"""
Core Utilities
Core SSH command execution utilities with session support.

NOTE: Session creation (connect/disconnect) is handled via WebSocket only.
AI cannot create new sessions - it can only use existing sessions via session_id.
This ensures credentials are always provided by user, not AI.

All command execution requires user approval before running.
"""

from typing import Optional
from ..config.session import RemctlSession
from ..config.tools import tool
from ...lib.gatekeeper import gatekeeper


@tool(name="server_exec")
async def execute_ssh_command(
    session_id: str,
    command: str,
    wait: float = 0.5,
) -> dict:
    """
    Execute a command on remote server via SSH in an existing session.

    Requires user approval before execution.

    Args:
        session_id: Session ID from WebSocket connection
        command: Command to execute
        wait: Wait time for output (default: 0.5s)

    Returns:
        Command output with stdout, stderr, and return code
    """
    # Create approval request (broadcast to all connected users)
    request = gatekeeper.create_request("server_exec", {"session_id": session_id, "command": command})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    # Execute command
    result = RemctlSession.execute(session_id, command, wait)
    return result
