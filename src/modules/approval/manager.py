"""
Approval Manager - Command approval system.
Requires user approval before AI tool execution.

Flow:
1. AI calls tool → Server creates approval request
2. Server sends request to user via WebSocket
3. User approves/rejects
4. Server executes tool (or returns rejection)
"""

import uuid
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime


class ApprovalRequest:
    """Represents a pending approval request."""

    def __init__(self, tool_name: str, params: Dict[str, Any], websocket=None):
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.tool_name = tool_name
        self.params = params
        self.websocket = websocket
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.event = asyncio.Event()
        self.approved: Optional[bool] = None
        self.reason: Optional[str] = None

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


# Global websocket registry for broadcasting approval requests
_active_websockets: List[Any] = []  # List of WebSocket connections


def register_websocket(ws):
    """Register a WebSocket connection for receiving approval requests."""
    if ws not in _active_websockets:
        _active_websockets.append(ws)


def unregister_websocket(ws):
    """Remove a WebSocket connection when disconnected."""
    if ws in _active_websockets:
        _active_websockets.remove(ws)


class ApprovalManager:
    """
    Manages approval requests for AI tool execution.

    Usage:
        approval = ApprovalManager()

        # Create request
        request = approval.create_request("db_query", {"query": "SELECT * FROM users"}, websocket)

        # Wait for approval
        approved = await approval.wait_for_approval(request.request_id, timeout=30)

        # User approves (via WebSocket handler)
        approval.approve(request.request_id)

        # Or reject
        approval.reject(request.request_id, reason="Dangerous query")
    """

    def __init__(self):
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._auto_approve_tools: set = {
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

    def create_request(self, tool_name: str, params: Dict[str, Any], websocket=None) -> ApprovalRequest:
        """
        Create a new approval request and broadcast to all connected users.

        Args:
            tool_name: Name of the tool being called
            params: Tool parameters
            websocket: User's WebSocket connection (optional, for direct send)

        Returns:
            ApprovalRequest instance
        """
        request = ApprovalRequest(tool_name, params, websocket)
        self._pending_requests[request.request_id] = request

        # Broadcast approval request to ALL connected users
        asyncio.create_task(self._broadcast_approval_request(request))

        return request

    async def _broadcast_approval_request(self, request: ApprovalRequest):
        """Broadcast approval request to all active WebSocket connections."""
        import json
        request_data = request.to_dict()

        for ws in _active_websockets[:]:  # Copy list to avoid modification during iteration
            try:
                await ws.send_json(request_data)
            except Exception:
                # WebSocket may be closed, remove from list
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
            # Wait for user response
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

    def approve(self, request_id: str):
        """Mark request as approved."""
        request = self._pending_requests.get(request_id)
        if request:
            request.approved = True
            request.event.set()

    def reject(self, request_id: str, reason: str = "User rejected the request"):
        """Mark request as rejected."""
        request = self._pending_requests.get(request_id)
        if request:
            request.approved = False
            request.reason = reason
            request.event.set()

    def needs_approval(self, tool_name: str) -> bool:
        """Check if a tool requires user approval."""
        return tool_name not in self._auto_approve_tools

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

    def _cleanup(self, request_id: str):
        """Remove request from storage."""
        self._pending_requests.pop(request_id, None)

    def cleanup_old_requests(self, max_age_seconds: int = 300):
        """Remove requests older than max_age_seconds."""
        import time
        current_time = time.time()
        to_remove = []

        for req_id, req in self._pending_requests.items():
            created_ts = datetime.strptime(req.created_at, "%Y-%m-%d %H:%M:%S").timestamp()
            if current_time - created_ts > max_age_seconds:
                to_remove.append(req_id)

        for req_id in to_remove:
            self._cleanup(req_id)


# Global instance
approval_manager = ApprovalManager()
