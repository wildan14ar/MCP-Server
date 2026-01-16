"""
Server MCP Routes
"""

from fastapi import APIRouter, WebSocket, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, List
from ..config.websocket_handler import ServerWebSocketHandler
from ..config.ssh_session import SSHSession

router = APIRouter(prefix="/server", tags=["server"])

# Global WebSocket handler
ws_handler = ServerWebSocketHandler()


# ============ TOKEN VALIDATION ============

async def validate_mcp_token(x_mcp_token: Optional[str] = Header(None)) -> str:
    """
    Validate MCP token from header.
    
    Usage:
        @router.post("/endpoint")
        async def endpoint(token: str = Depends(validate_mcp_token)):
            # token is validated
    """
    if not x_mcp_token:
        raise HTTPException(
            status_code=401, 
            detail="Missing MCP token. Include 'X-MCP-Token' header."
        )
    
    if not ws_handler.validate_token(x_mcp_token):
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired MCP token"
        )
    
    return x_mcp_token


# ============ MODELS ============

class ConnectRequest(BaseModel):
    """SSH connection request."""
    host: str
    user: str
    password: Optional[str] = None
    pkey_str: Optional[str] = None
    port: int = 22
    timeout: int = 10


class ExecuteRequest(BaseModel):
    """Command execution request."""
    host: str
    user: str
    password: Optional[str] = None
    pkey_str: Optional[str] = None
    port: int = 22
    command: str
    wait: float = 0.5


class ExecuteResponse(BaseModel):
    """Command execution response."""
    stdout: str
    stderr: str
    returncode: int
    session_id: str
    token: str


class TokenExecuteRequest(BaseModel):
    """Token-based command execution request."""
    command: str
    wait: float = 0.5


# ============ WEBSOCKET ============

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time server communication.
    
    Protocol:
    - Client connects to ws://host:port/server/ws
    - Client sends: {"type": "connect", "host": "...", "user": "...", "password": "..."}
    - Server sends: {"type": "connected", "session_id": "...", "token": "..."}
    - Client sends: {"type": "input", "data": "ls\\n"}
    - Server streams: {"type": "output", "data": "..."}
    - Client sends: {"type": "execute", "command": "pwd"}
    - Server sends: {"type": "result", "stdout": "...", "token": "..."}
    - Client sends: {"type": "disconnect"}
    
    Note: Token is returned in 'connected' and 'result' messages.
          Use this token for subsequent MCP API calls.
    """
    await ws_handler.handle_connection(websocket)


# ============ REST API ============

@router.post("/connect", summary="Test SSH connection")
async def test_connection(request: ConnectRequest):
    """
    Test SSH connection.
    Returns connection status and session info.
    """
    session = SSHSession(
        host=request.host,
        user=request.user,
        password=request.password,
        pkey_str=request.pkey_str,
        port=request.port,
        timeout=request.timeout,
    )
    
    try:
        session.connect()
        session_id = session.session_id
        session.close()
        
        return {
            "status": "success",
            "message": "Connection successful",
            "session_id": session_id,
            "host": request.host,
            "user": request.user
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


@router.post("/execute", response_model=ExecuteResponse, summary="Execute command via SSH")
async def execute_command(request: ExecuteRequest):
    """
    Execute single command via SSH, returns result with token, and closes session.
    
    **Returns token** that can be used for subsequent MCP operations.
    
    For interactive sessions, use WebSocket endpoint instead.
    """
    session = SSHSession(
        host=request.host,
        user=request.user,
        password=request.password,
        pkey_str=request.pkey_str,
        port=request.port,
    )
    
    try:
        session.connect()
        result = session.execute(request.command, wait=request.wait)
        session.close()
        
        return ExecuteResponse(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
            session_id=result.session_id,
            token=result.token
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.post("/mcp/execute", response_model=ExecuteResponse, summary="Execute command using MCP token")
async def mcp_execute_command(
    request: TokenExecuteRequest,
    token: str = Depends(validate_mcp_token)
):
    """
    Execute command using MCP token (from WebSocket session).
    
    **Requires MCP token** in 'X-MCP-Token' header.
    
    Token is obtained from WebSocket 'connected' or 'result' messages.
    
    This endpoint allows you to execute commands in an existing WebSocket session
    using the token received when connecting.
    
    Example:
    ```
    POST /server/mcp/execute
    Headers:
      X-MCP-Token: your_token_here
    Body:
      {
        "command": "ls -la",
        "wait": 0.5
      }
    ```
    """
    session = ws_handler.get_session_by_token(token)
    
    if not session or not session.is_connected():
        raise HTTPException(
            status_code=404,
            detail="Session not found or not connected"
        )
    
    try:
        result = session.execute(request.command, wait=request.wait)
        
        return ExecuteResponse(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
            session_id=result.session_id,
            token=token
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.get("/mcp/validate", summary="Validate MCP token")
async def validate_token_endpoint(token: str = Depends(validate_mcp_token)):
    """
    Validate MCP token.
    
    **Requires MCP token** in 'X-MCP-Token' header.
    
    Returns session info if token is valid.
    """
    session = ws_handler.get_session_by_token(token)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "valid": True,
        "session_id": session.session_id,
        "host": session.host,
        "user": session.user,
        "connected": session.is_connected()
    }


@router.get("/sessions", summary="Get active WebSocket sessions")
async def get_sessions():
    """
    Get list of active WebSocket server sessions.
    """
    return {
        "sessions": ws_handler.get_active_sessions(),
        "count": len(ws_handler.sessions)
    }


@router.get("/health", summary="Health check")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "server-mcp",
        "active_sessions": len(ws_handler.sessions)
    }
