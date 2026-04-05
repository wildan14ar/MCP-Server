"""
Approval Module
Command approval system - requires user approval before AI tool execution.

Usage:
    from src.modules.approval import approval_manager, register_websocket
    
    # Register websocket for receiving approval requests
    register_websocket(websocket)
    
    # Create request
    request = approval_manager.create_request("db_query", {"query": "SELECT * FROM users"})
    
    # Wait for approval
    result = await approval_manager.wait_for_approval(request.request_id)
    
    # User approves via WebSocket
    approval_manager.approve(request.request_id)
"""

from .manager import (
    ApprovalManager,
    ApprovalRequest,
    approval_manager,
    register_websocket,
    unregister_websocket,
    _active_websockets,
)

__all__ = [
    "ApprovalManager",
    "ApprovalRequest",
    "approval_manager",
    "register_websocket",
    "unregister_websocket",
    "_active_websockets",
]
