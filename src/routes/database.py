"""
Database Routes
WebSocket + MCP server registration for database module.

Endpoints:
- WebSocket: ws://localhost:8017/database/ws         (User only - creates session)
- MCP:       http://localhost:8017/database/mcp      (AI only - uses existing session)

Security:
- User creates connection via WebSocket with credentials
- AI receives connection_id + token to use existing connection
- AI CANNOT create new connections (no credential exposure)
- ALL AI actions require user approval before execution
"""

import json
import asyncio
from typing import Dict, Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, FastAPI
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP

from src.modules.database.config.connection import DatabaseConnection
from src.modules.database.config.tools import ToolsManager
from src.modules.database.config.skills import SkillsManager
from src.modules.database.tools.session_mgmt import register_session_tools
from src.lib.gatekeeper import gatekeeper, register_websocket, unregister_websocket, store_credentials, remove_credentials

# MCP instance
mcp = FastMCP("database")

# Router
router = APIRouter(prefix="/database", tags=["database"])

# Global mapping: token → connection (for AI access)
_token_to_connection: Dict[str, DatabaseConnection] = {}

# Global websocket registry (for sending approval requests to user)
_active_websockets: Dict[str, WebSocket] = {}  # token → websocket


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket for real-time database session (USER ONLY).
    User creates connection with credentials → gets token → shares with AI.
    """
    await websocket.accept()
    
    # Register websocket for receiving approval requests
    register_websocket(websocket)
    
    connections: Dict[str, DatabaseConnection] = {}
    active_connection: Optional[DatabaseConnection] = None

    try:
        while True:
            data = json.loads(await websocket.receive_text())
            msg_type = data.get("type")

            if msg_type == "connect":
                if active_connection:
                    await websocket.send_json(
                        {"type": "error", "message": "Already connected"}
                    )
                    continue

                try:
                    conn = DatabaseConnection(
                        db_type=data.get("db_type", "postgresql"),
                        host=data.get("host"),
                        user=data.get("user"),
                        password=data.get("password"),
                        database=data.get("database", ""),
                        port=data.get("port", 5432),
                        schema=data.get("schema"),
                    )
                    conn.connect()
                    connections[conn.connection_id] = conn
                    connections[conn.token] = conn
                    _token_to_connection[conn.token] = conn
                    _active_websockets[conn.token] = websocket
                    active_connection = conn

                    # Store credentials for AI to use later (NO credentials sent via MCP)
                    store_credentials(conn.token, "database", {
                        "user": data.get("user"),
                        "password": data.get("password"),
                    })

                    await websocket.send_json(
                        {
                            "type": "connected",
                            "connection_id": conn.connection_id,
                            "token": conn.token,
                            "db_type": conn.db_type,
                            "host": conn.host,
                            "database": conn.database,
                            "message": "Connection created. Share 'connection_id' and 'token' with AI to use this session. All AI actions will require your approval."
                        }
                    )
                except Exception as e:
                    await websocket.send_json(
                        {"type": "error", "message": str(e)}
                    )

            elif msg_type == "query":
                if not active_connection:
                    await websocket.send_json(
                        {"type": "error", "message": "Not connected"}
                    )
                    continue

                try:
                    result = active_connection.execute(
                        data.get("query", ""),
                        data.get("params"),
                    )

                    await websocket.send_json(
                        {
                            "type": "result",
                            "success": result.success,
                            "columns": result.columns,
                            "rows": result.rows[:100],  # Limit display
                            "row_count": result.row_count,
                            "execution_time": result.execution_time,
                            "error": result.error,
                        }
                    )
                except Exception as e:
                    await websocket.send_json(
                        {"type": "error", "message": str(e)}
                    )

            elif msg_type == "schema":
                if not active_connection:
                    await websocket.send_json(
                        {"type": "error", "message": "Not connected"}
                    )
                    continue

                try:
                    schema = active_connection.get_schema_info(
                        data.get("table_name")
                    )

                    await websocket.send_json(
                        {
                            "type": "schema_result",
                            "schema": schema,
                        }
                    )
                except Exception as e:
                    await websocket.send_json(
                        {"type": "error", "message": str(e)}
                    )

            elif msg_type == "transaction_start":
                if not active_connection:
                    await websocket.send_json(
                        {"type": "error", "message": "Not connected"}
                    )
                    continue

                try:
                    active_connection.begin_transaction()
                    await websocket.send_json(
                        {"type": "transaction_started"}
                    )
                except Exception as e:
                    await websocket.send_json(
                        {"type": "error", "message": str(e)}
                    )

            elif msg_type == "transaction_commit":
                if not active_connection:
                    await websocket.send_json(
                        {"type": "error", "message": "Not connected"}
                    )
                    continue

                try:
                    active_connection.commit_transaction()
                    await websocket.send_json(
                        {"type": "transaction_committed"}
                    )
                except Exception as e:
                    await websocket.send_json(
                        {"type": "error", "message": str(e)}
                    )

            elif msg_type == "transaction_rollback":
                if not active_connection:
                    await websocket.send_json(
                        {"type": "error", "message": "Not connected"}
                    )
                    continue

                try:
                    active_connection.rollback_transaction()
                    await websocket.send_json(
                        {"type": "transaction_rolled_back"}
                    )
                except Exception as e:
                    await websocket.send_json(
                        {"type": "error", "message": str(e)}
                    )

            elif msg_type == "tables":
                if not active_connection:
                    await websocket.send_json(
                        {"type": "error", "message": "Not connected"}
                    )
                    continue

                try:
                    schema = active_connection.get_schema_info()
                    tables = list(schema.keys())
                    await websocket.send_json(
                        {
                            "type": "tables_result",
                            "tables": tables,
                            "total": len(tables),
                        }
                    )
                except Exception as e:
                    await websocket.send_json(
                        {"type": "error", "message": str(e)}
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
        
        # Cleanup all connections created in this session
        for conn_id, conn in connections.items():
            try:
                _token_to_connection.pop(conn.token, None)
                _active_websockets.pop(conn.token, None)
                remove_credentials(conn.token)
                DatabaseConnection.close(conn.connection_id)
            except Exception:
                pass


def setup_database(app: FastAPI):
    """
    Setup complete Database (MCP + WebSocket) in ONE call.
    
    Usage:
        from src.routes import setup_database
        setup_database(app)
    """
    # Register MCP tools (AI can only use existing sessions)
    ToolsManager().get_tools(mcp)
    SkillsManager().get_tools(mcp)
    register_session_tools(mcp)

    # Mount MCP SSE at /database/mcp
    app.router.routes.append(Mount("/database/mcp", app=mcp.streamable_http_app()))

    # Include WebSocket router
    app.include_router(router)
