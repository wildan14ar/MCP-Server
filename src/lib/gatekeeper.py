"""
Gatekeeper - Access Control Library

Central approval system for AI tool execution.
All AI actions require user approval before execution (except read-only tools).

Usage:
    from src.lib.gatekeeper import gatekeeper, register_websocket, unregister_websocket

    # Register websocket for receiving approval requests
    register_websocket(websocket)

    # Create request
    request = gatekeeper.create_request("db_query", {"query": "SELECT * FROM users"})

    # Wait for approval
    result = await gatekeeper.wait_for_approval(request.request_id)

    # User approves via WebSocket handler
    gatekeeper.approve(request.request_id)
"""

import uuid
import asyncio
import time
import json
from typing import Dict, Optional, Any, List


# ─── WebSocket Registry ───────────────────────────────────────────────────────

_active_websockets: List[Any] = []


def register_websocket(ws: Any) -> None:
    """Register a WebSocket connection for receiving approval requests."""
    if ws not in _active_websockets:
        _active_websockets.append(ws)


def unregister_websocket(ws: Any) -> None:
    """Remove a WebSocket connection when disconnected."""
    if ws in _active_websockets:
        _active_websockets.remove(ws)


def get_active_websockets() -> List[Any]:
    """Get list of all active WebSocket connections."""
    return _active_websockets[:]


def count_active_connections() -> int:
    """Get number of active WebSocket connections."""
    return len(_active_websockets)


# ─── Credential Store (per token) ─────────────────────────────────────────────

# Maps token → stored credentials (set by WS, read by MCP tools)
_credentials_store: Dict[str, Dict[str, Any]] = {}

# Active credentials reference - set when user connects via WS
# MCP tools use this to get credentials without knowing the token
_active_creds: Dict[str, Optional[Dict[str, Any]]] = {
    "remctl": None,
    "database": None,
}


def store_credentials(token: str, module: str, creds: Dict[str, Any]) -> None:
    """
    Store credentials for a session token.
    Called by WebSocket handler when user connects.

    Args:
        token: Session token
        module: "remctl" or "database"
        creds: Credentials dict (host, user, password, pkey_str, port, etc.)
    """
    if token not in _credentials_store:
        _credentials_store[token] = {}
    _credentials_store[token][module] = creds

    # Also set as active credentials for MCP tools to use
    _active_creds[module] = creds


def get_credentials(module: str) -> Optional[Dict[str, Any]]:
    """
    Get stored credentials for MCP tools.
    Uses the active credentials set by the last WS connection.

    Args:
        module: "remctl" or "database"

    Returns:
        Credentials dict or None
    """
    return _active_creds.get(module)


def remove_credentials(token: str) -> None:
    """Remove credentials when session disconnects."""
    stored = _credentials_store.pop(token, None)
    if stored:
        # If the removed token's creds match active creds, clear active
        for module in ["remctl", "database"]:
            if stored.get(module) == _active_creds.get(module):
                _active_creds[module] = None


# ─── Access Request ────────────────────────────────────────────────────────────

class AccessRequest:
    """Represents a pending access/request for approval."""

    def __init__(self, tool_name: str, params: Dict[str, Any], websocket=None):
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.tool_name = tool_name
        self.params = params
        self.websocket = websocket
        self.created_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self.event = asyncio.Event()
        self.approved: bool | None = None
        self.reason: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for WebSocket message."""
        return {
            "type": "approval_request",
            "request_id": self.request_id,
            "tool": self.tool_name,
            "params": self.params,
            "created_at": self.created_at,
            "message": f"AI wants to execute: {self.tool_name}"
        }


# ─── Gatekeeper ────────────────────────────────────────────────────────────────

class Gatekeeper:
    """
    Manages approval requests for AI tool execution.

    Usage:
        from src.lib.gatekeeper import gatekeeper

        # Create request (auto-broadcasts to all connected users)
        request = gatekeeper.create_request("db_query", {"query": "SELECT * FROM users"})

        # Wait for approval
        result = await gatekeeper.wait_for_approval(request.request_id, timeout=30)

        # User approves via WebSocket handler
        gatekeeper.approve(request.request_id)

        # Or reject
        gatekeeper.reject(request.request_id, reason="Dangerous query")
    """

    def __init__(self):
        self._pending_requests: Dict[str, AccessRequest] = {}
        self._auto_approve_tools: set = {
            # Session management (no approval needed - credentials from WS)
            "server_new_session",
            "server_list_sessions",
            "server_close_session",
            "db_new_connection",
            "db_list_connections",
            "db_close_connection",
            # Read-only tools (no approval needed)
            "db_tables",
            "db_schema",
            "db_columns",
            "db_primary_key",
            "db_foreign_keys",
            "db_indexes",
            "db_relationships",
            "db_table_stats",
            "db_column_types",
            "db_search_tables",
            "db_connection_info",
            "get_skills",
            "load_skill",
        }

    # ── Request Lifecycle ─────────────────────────────────────────────────

    def create_request(self, tool_name: str, params: Dict[str, Any], websocket=None) -> AccessRequest:
        """
        Create a new approval request and broadcast to all connected users.

        Args:
            tool_name: Name of the tool being called
            params: Tool parameters
            websocket: User's WebSocket connection (optional, for direct send)

        Returns:
            AccessRequest instance
        """
        request = AccessRequest(tool_name, params, websocket)
        self._pending_requests[request.request_id] = request
        asyncio.create_task(self._broadcast_approval_request(request))
        return request

    async def _broadcast_approval_request(self, request: AccessRequest) -> None:
        """Broadcast approval request to all active WebSocket connections."""
        request_data = request.to_dict()

        for ws in _active_websockets[:]:
            try:
                await ws.send_json(request_data)
            except Exception:
                if ws in _active_websockets:
                    _active_websockets.remove(ws)

    async def wait_for_approval(self, request_id: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Wait for user approval with timeout.

        Args:
            request_id: Request ID to wait for
            timeout: Timeout in seconds (default: 60)

        Returns:
            Dict with approval status and reason (if rejected)
        """
        request = self._pending_requests.get(request_id)
        if not request:
            return {"approved": False, "reason": "Request not found"}

        try:
            await asyncio.wait_for(request.event.wait(), timeout=timeout)
            if request.approved:
                return {"approved": True}
            else:
                return {
                    "approved": False,
                    "reason": request.reason or "User rejected the request"
                }
        except asyncio.TimeoutError:
            self._cleanup(request_id)
            return {
                "approved": False,
                "reason": f"Approval request timed out after {timeout}s"
            }

    def approve(self, request_id: str) -> None:
        """Mark request as approved."""
        request = self._pending_requests.get(request_id)
        if request:
            request.approved = True
            request.event.set()

    def reject(self, request_id: str, reason: str = "User rejected the request") -> None:
        """Mark request as rejected."""
        request = self._pending_requests.get(request_id)
        if request:
            request.approved = False
            request.reason = reason
            request.event.set()

    # ── Utility ───────────────────────────────────────────────────────────

    def needs_approval(self, tool_name: str) -> bool:
        """Check if a tool requires user approval."""
        return tool_name not in self._auto_approve_tools

    def get_request(self, request_id: str) -> Optional[AccessRequest]:
        """Get a specific request by ID."""
        return self._pending_requests.get(request_id)

    def get_pending_count(self) -> int:
        """Get number of pending requests."""
        return sum(1 for req in self._pending_requests.values() if not req.event.is_set())

    def list_pending(self) -> list:
        """List all pending approval requests."""
        return [
            req.to_dict()
            for req in self._pending_requests.values()
            if not req.event.is_set()
        ]

    def set_auto_approve(self, tool_names: set) -> None:
        """Set the list of tools that auto-approve (skip approval)."""
        self._auto_approve_tools = tool_names.copy()

    def add_auto_approve(self, tool_name: str) -> None:
        """Add a tool to the auto-approve list."""
        self._auto_approve_tools.add(tool_name)

    def remove_auto_approve(self, tool_name: str) -> None:
        """Remove a tool from the auto-approve list."""
        self._auto_approve_tools.discard(tool_name)

    def _cleanup(self, request_id: str) -> None:
        """Remove request from storage."""
        self._pending_requests.pop(request_id, None)

    def cleanup_old_requests(self, max_age_seconds: int = 300) -> None:
        """Remove requests older than max_age_seconds."""
        current_time = time.time()
        to_remove = []

        for req_id, req in self._pending_requests.items():
            created_ts = time.mktime(
                time.strptime(req.created_at, "%Y-%m-%d %H:%M:%S")
            )
            if current_time - created_ts > max_age_seconds:
                to_remove.append(req_id)

        for req_id in to_remove:
            self._cleanup(req_id)


# ── Global Singleton ──────────────────────────────────────────────────────────

gatekeeper = Gatekeeper()
