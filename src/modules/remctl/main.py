"""
Remctl Module Routes
Export single router for inclusion in main server.

Usage:
    from src.modules.remctl import remctl_router, mcp
    
    app.include_router(remctl_router)
"""

import json
import asyncio
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from mcp.server.fastmcp import FastMCP
from .config.session import RemctlSession
from .config.tools import ToolsManager
from .config.skills import SkillsManager


# ============ REMCTL ROUTER (Combined) ============

remctl_router = APIRouter(prefix="/remctl", tags=["remctl"])

# WebSocket endpoint
@remctl_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time terminal session."""
    await websocket.accept()
    session: Optional[RemctlSession] = None
    token_sessions: Dict[str, RemctlSession] = {}
    
    try:
        while True:
            data = json.loads(await websocket.receive_text())
            msg_type = data.get("type")
            
            if msg_type == "connect":
                if session:
                    await websocket.send_json({"type": "error", "message": "Already connected"})
                    continue
                
                session = RemctlSession(
                    host=data.get("host"),
                    user=data.get("user"),
                    password=data.get("password"),
                    pkey_str=data.get("pkey_str"),
                    port=data.get("port", 22),
                    on_output=lambda out: asyncio.create_task(websocket.send_json({"type": "output", "data": out}))
                )
                session.connect()
                token_sessions[session.token] = session
                
                await websocket.send_json({
                    "type": "connected",
                    "session_id": session.session_id,
                    "token": session.token,
                    "host": session.host,
                    "user": session.user
                })
            
            elif msg_type == "execute":
                if not session:
                    await websocket.send_json({"type": "error", "message": "Not connected"})
                    continue
                
                result = session.execute(data.get("command", ""), wait=data.get("wait", 0.5))
                await websocket.send_json({
                    "type": "result",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "session_id": result.session_id,
                    "token": result.token
                })
            
            elif msg_type == "disconnect":
                break
    
    except WebSocketDisconnect:
        pass
    finally:
        if session:
            token_sessions.pop(session.token, None)
            session.close()


# MCP endpoint
mcp = FastMCP("remctl")

@remctl_router.post("/mcp")
async def mcp_endpoint():
    """MCP server endpoint - register and return tools."""
    # Register tools on-demand
    ToolsManager().get_tools(mcp)
    SkillsManager().get_tools(mcp)
    
    # Session tools
    @mcp.tool(name="create_session")
    async def create_session(
        host: str, user: str,
        password: str = None, pkey_str: str = None, port: int = 22,
    ) -> dict:
        try:
            sid = RemctlSession.create(host, user, password, pkey_str, port)
            return {"status": "success", "session_id": sid, "host": host}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @mcp.tool(name="list_sessions")
    async def list_sessions() -> dict:
        return {"status": "success", "sessions": RemctlSession.list()}
    
    @mcp.tool(name="execute_session")
    async def execute_session(session_id: str, command: str, wait: float = 0.5) -> dict:
        return RemctlSession.execute(session_id, command, wait)
    
    @mcp.tool(name="get_snapshot")
    async def get_snapshot(session_id: str) -> dict:
        return RemctlSession.snapshot(session_id)
    
    @mcp.tool(name="close_session")
    async def close_session(session_id: str) -> dict:
        return {"status": "success" if RemctlSession.close(session_id) else "error"}
    
    return {
        "status": "success",
        "message": "Remctl MCP Server",
        "tools": len(mcp._tool_manager._tools),
        "endpoint": "/remctl/mcp"
    }


# Exports
__all__ = ["remctl_router", "mcp"]
