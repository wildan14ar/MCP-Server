"""
Remctl Routes
WebSocket + MCP server registration for remote control module.

Endpoints:
- WebSocket: ws://localhost:8017/remctl/ws         (User only - creates session)
- MCP:       http://localhost:8017/remctl/mcp      (AI only - uses existing session)

Security:
- User creates SSH session via WebSocket with credentials
- AI receives session_id + token to use existing session
- AI CANNOT create new sessions (no credential exposure)
"""

import json
import asyncio
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, FastAPI
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP

from src.modules.remctl.config.session import RemctlSession
from src.modules.remctl.config.tools import ToolsManager
from src.modules.remctl.config.skills import SkillsManager
from src.modules.remctl.tools.session_mgmt import register_session_tools
from src.lib.gatekeeper import gatekeeper, register_websocket, unregister_websocket, store_credentials, remove_credentials

# MCP instance
mcp = FastMCP("remctl")

# Router
router = APIRouter(prefix="/remctl", tags=["remctl"])

# Global mapping: token → session (for AI access)
_token_to_session: Dict[str, RemctlSession] = {}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket for real-time terminal session (USER ONLY).
    User creates SSH session with credentials → gets token → shares with AI.
    """
    await websocket.accept()
    
    # Register websocket for receiving approval requests
    register_websocket(websocket)
    
    session: Optional[RemctlSession] = None
    token_sessions: Dict[str, RemctlSession] = {}

    try:
        while True:
            data = json.loads(await websocket.receive_text())
            msg_type = data.get("type")

            if msg_type == "connect":
                if session:
                    await websocket.send_json(
                        {"type": "error", "message": "Already connected"}
                    )
                    continue

                try:
                    session = RemctlSession(
                        host=data.get("host"),
                        user=data.get("user"),
                        password=data.get("password"),
                        pkey_str=data.get("pkey_str"),
                        port=data.get("port", 22),
                        on_output=lambda out: asyncio.create_task(
                            websocket.send_json({"type": "output", "data": out})
                        ),
                    )
                    session.connect()
                    token_sessions[session.token] = session
                    _token_to_session[session.token] = session

                    # Store credentials for AI to use later (NO credentials sent via MCP)
                    store_credentials(session.token, "remctl", {
                        "user": data.get("user"),
                        "password": data.get("password"),
                        "pkey_str": data.get("pkey_str"),
                    })

                    await websocket.send_json(
                        {
                            "type": "connected",
                            "session_id": session.session_id,
                            "token": session.token,
                            "host": session.host,
                            "user": session.user,
                            "message": "Session created. Share 'session_id' and 'token' with AI to use this session. All AI actions will require your approval."
                        }
                    )
                except Exception as e:
                    await websocket.send_json(
                        {"type": "error", "message": str(e)}
                    )

            elif msg_type == "execute":
                if not session:
                    await websocket.send_json(
                        {"type": "error", "message": "Not connected"}
                    )
                    continue

                result = session.execute(
                    data.get("command", ""), wait=data.get("wait", 0.5)
                )
                await websocket.send_json(
                    {
                        "type": "result",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                        "session_id": result.session_id,
                        "token": result.token,
                    }
                )

            elif msg_type == "disconnect":
                break

            elif msg_type == "approve_command":
                # User approves or rejects AI request
                request_id = data.get("request_id")
                approved = data.get("approved", False)
                reason = data.get("reason")

                if approved:
                    gatekeeper.approve(request_id)
                else:
                    gatekeeper.reject(request_id, reason or "User rejected the request")

                await websocket.send_json({
                    "type": "approval_response",
                    "request_id": request_id,
                    "status": "approved" if approved else "rejected"
                })

            elif msg_type == "list_pending":
                # User requests list of pending approvals
                pending = gatekeeper.list_pending()
                await websocket.send_json({
                    "type": "pending_list",
                    "requests": pending,
                    "total": len(pending)
                })

    except WebSocketDisconnect:
        pass
    finally:
        # Unregister websocket
        unregister_websocket(websocket)

        if session:
            token_sessions.pop(session.token, None)
            _token_to_session.pop(session.token, None)
            remove_credentials(session.token)
            RemctlSession.close(session.session_id)


def setup_remctl(app: FastAPI):
    """
    Setup complete Remctl (MCP + WebSocket) in ONE call.
    
    Usage:
        from src.routes import setup_remctl
        setup_remctl(app)
    """
    # Register MCP tools (AI can only use existing sessions)
    ToolsManager().get_tools(mcp)
    SkillsManager().get_tools(mcp)
    register_session_tools(mcp)

    # Mount MCP SSE at /remctl/mcp
    app.router.routes.append(Mount("/remctl/mcp", app=mcp.streamable_http_app()))

    # Include WebSocket router
    app.include_router(router)
