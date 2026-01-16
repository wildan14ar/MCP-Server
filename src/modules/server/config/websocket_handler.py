"""
WebSocket Handler for Real-time Terminal Communication
"""

import json
import asyncio
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from .ssh_session import SSHSession


class ServerWebSocketHandler:
    """
    WebSocket handler for real-time server communication.
    
    Features:
    - Real-time output streaming
    - Interactive input
    - Session management
    - Multi-client support
    
    Protocol:
    Client -> Server:
        {"type": "connect", "host": "...", "user": "...", "password": "..."}
        {"type": "input", "data": "ls -la\\n"}
        {"type": "execute", "command": "pwd"}
        {"type": "disconnect"}
    
    Server -> Client:
        {"type": "connected", "session_id": "..."}
        {"type": "output", "data": "..."}
        {"type": "result", "stdout": "...", "stderr": "...", "returncode": 0}
        {"type": "error", "message": "..."}
        {"type": "disconnected"}
    """
    
    def __init__(self):
        # Active sessions: {websocket_id: SSHSession}
        self.sessions: Dict[int, SSHSession] = {}
        # Token to session mapping: {token: SSHSession}
        self.token_sessions: Dict[str, SSHSession] = {}
    
    async def handle_connection(self, websocket: WebSocket):
        """Handle WebSocket connection for terminal session."""
        await websocket.accept()
        ws_id = id(websocket)
        session: Optional[SSHSession] = None
        
        try:
            while True:
                # Receive message from client
                message = await websocket.receive_text()
                data = json.loads(message)
                msg_type = data.get("type")
                
                # Handle connect
                if msg_type == "connect":
                    if session:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Already connected"
                        })
                        continue
                    
                    host = data.get("host")
                    user = data.get("user")
                    password = data.get("password")
                    pkey_str = data.get("pkey_str")
                    port = data.get("port", 22)
                    
                    if not host or not user:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Missing host or user"
                        })
                        continue
                    
                    # Create output callback for streaming
                    async def output_callback(output: str):
                        try:
                            await websocket.send_json({
                                "type": "output",
                                "data": output
                            })
                        except:
                            pass
                    
                    # Create SSH session
                    session = SSHSession(
                        host=host,
                        user=user,
                        password=password,
                        pkey_str=pkey_str,
                        port=port,
                        on_output=lambda out: asyncio.create_task(output_callback(out))
                    )
                    
                    try:
                        session.connect()
                        self.sessions[ws_id] = session
                        self.token_sessions[session.token] = session
                        
                        await websocket.send_json({
                            "type": "connected",
                            "session_id": session.session_id,
                            "token": session.token,
                            "host": host,
                            "user": user
                        })
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Connection failed: {str(e)}"
                        })
                
                # Handle input (interactive typing)
                elif msg_type == "input":
                    if not session or not session.is_connected():
                        await websocket.send_json({
                            "type": "error",
                            "message": "Not connected"
                        })
                        continue
                    
                    input_data = data.get("data", "")
                    session.send_input(input_data)
                
                # Handle execute (command with result)
                elif msg_type == "execute":
                    if not session or not session.is_connected():
                        await websocket.send_json({
                            "type": "error",
                            "message": "Not connected"
                        })
                        continue
                    
                    command = data.get("command", "")
                    wait = data.get("wait", 0.5)
                    skip_confirm = data.get("skip_confirm", False)
                    
                    # Check if confirmation is required
                    if not skip_confirm:
                        # Generate confirmation ID
                        confirm_id = str(uuid.uuid4())[:8]
                        
                        # Store pending confirmation
                        self.pending_confirmations[confirm_id] = {
                            "command": command,
                            "wait": wait,
                            "websocket": websocket,
                            "session": session
                        }
                        
                        # Send confirmation request
                        await websocket.send_json({
                            "type": "confirm_required",
                            "confirm_id": confirm_id,
                            "command": command,
                            "message": f"Execute command: {command}?",
                            "warning": self._get_command_warning(command)
                        })
                        continue
                    
                    # Execute without confirmation (skip_confirm=true)
                    try:
                        result = session.execute(command, wait=wait)
                        await websocket.send_json({
                            "type": "result",
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "returncode": result.returncode,
                            "session_id": result.session_id,
                            "token": result.token
                        })
                    except PermissionError as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e)
                        })
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Execution failed: {str(e)}"
                        })
                
                # Handle confirmation response
                elif msg_type == "confirm_execute":
                    confirm_id = data.get("confirm_id")
                    approved = data.get("approved", False)
                    
                    if not confirm_id or confirm_id not in self.pending_confirmations:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid or expired confirmation ID"
                        })
                        continue
                    
                    # Get pending command
                    pending = self.pending_confirmations.pop(confirm_id)
                    command = pending["command"]
                    wait = pending["wait"]
                    pending_session = pending["session"]
                    
                    if not approved:
                        # User cancelled
                        await websocket.send_json({
                            "type": "cancelled",
                            "command": command,
                            "message": "Command execution cancelled by user"
                        })
                        continue
                    
                    # User approved - execute command
                    if not pending_session or not pending_session.is_connected():
                        await websocket.send_json({
                            "type": "error",
                            "message": "Session disconnected"
                        })
                        continue
                    
                    try:
                        result = pending_session.execute(command, wait=wait)
                        await websocket.send_json({
                            "type": "result",
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "returncode": result.returncode,
                            "session_id": result.session_id,
                            "token": result.token,
                            "confirmed": True
                        })
                    except PermissionError as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e)
                        })
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Execution failed: {str(e)}"
                        })
                
                # Handle disconnect
                elif msg_type == "disconnect":
                    if session:
                        if session.token in self.token_sessions:
                            del self.token_sessions[session.token]
                        session.close()
                        del self.sessions[ws_id]
                        session = None
                    
                    await websocket.send_json({
                        "type": "disconnected"
                    })
                    break
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}"
                    })
        
        except WebSocketDisconnect:
            pass
        except Exception as e:
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            except:
                pass
        finally:
            # Cleanup
            if ws_id in self.sessions:
                if self.sessions[ws_id]:
                    session_to_clean = self.sessions[ws_id]
                    if session_to_clean.token in self.token_sessions:
                        del self.token_sessions[session_to_clean.token]
                    session_to_clean.close()
                del self.sessions[ws_id]
    
    def _get_command_warning(self, command: str) -> Optional[str]:
        """
        Get warning message for potentially dangerous commands.
        
        Returns warning message or None if command is safe.
        """
        dangerous_commands = {
            "rm": "⚠️ WARNING: This command can delete files permanently!",
            "rmdir": "⚠️ WARNING: This command will remove directories!",
            "dd": "⚠️ DANGER: This command can overwrite disk data!",
            "mkfs": "⚠️ DANGER: This command will format a disk!",
            "shutdown": "⚠️ WARNING: This will shutdown the system!",
            "reboot": "⚠️ WARNING: This will reboot the system!",
            "halt": "⚠️ WARNING: This will halt the system!",
            "poweroff": "⚠️ WARNING: This will power off the system!",
            "kill": "⚠️ WARNING: This will terminate processes!",
            "killall": "⚠️ WARNING: This will kill multiple processes!",
            "chmod": "⚠️ WARNING: This will change file permissions!",
            "chown": "⚠️ WARNING: This will change file ownership!",
            "mv": "⚠️ WARNING: This command can move/rename files!",
            "format": "⚠️ DANGER: This command will format a disk!",
            ">": "⚠️ WARNING: This will overwrite file contents!",
        }
        
        cmd_lower = command.lower().strip()
        
        # Check for dangerous commands
        for danger_cmd, warning in dangerous_commands.items():
            if cmd_lower.startswith(danger_cmd) or f" {danger_cmd} " in cmd_lower:
                return warning
        
        # Check for dangerous flags
        if "-rf" in cmd_lower or "-fr" in cmd_lower:
            return "⚠️ DANGER: Force recursive operation detected!"
        
        if "/*" in cmd_lower or "/ " in cmd_lower:
            return "⚠️ DANGER: Root directory operation detected!"
        
        return None
    
    def get_session_by_token(self, token: str) -> Optional[SSHSession]:
        """Get session by token."""
        return self.token_sessions.get(token)
    
    def validate_token(self, token: str) -> bool:
        """Validate if token exists and session is active."""
        session = self.token_sessions.get(token)
        return session is not None and session.is_connected()
    
    def get_active_sessions(self) -> list:
        """Get list of active sessions."""
        return [
            {
                "session_id": session.session_id,
                "host": session.host,
                "user": session.user,
                "connected": session.is_connected(),
                "has_token": bool(session.token)
            }
            for session in self.sessions.values()
        ]
    
    def close_all(self):
        """Close all active sessions."""
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()
        self.token_sessions.clear()
        self.pending_confirmations.clear()
