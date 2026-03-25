"""
RemctlSession - Unified SSH session manager.
Single class for creating, managing, and executing commands in SSH sessions.

Features:
- Create multiple sessions (credentials stored automatically)
- Execute commands by session ID (no credentials needed!)
- List sessions, get snapshots, close sessions
- All in ONE class

Usage:
    # Create session (credentials stored automatically)
    session_id = RemctlSession.create(host="...", user="...", password="...")
    
    # Execute (NO credentials - auto from stored session!)
    result = RemctlSession.execute(session_id, "ls -la")
    
    # List all sessions
    sessions = RemctlSession.list()
    
    # Get snapshot
    snapshot = RemctlSession.snapshot(session_id)
"""

import io
import time
import uuid
import secrets
import threading
from dataclasses import dataclass, asdict
from queue import Queue, Empty
from typing import Optional, List, Callable, Dict
from datetime import datetime
import paramiko


@dataclass
class SessionResult:
    """Result of command execution."""
    stdout: str
    stderr: str
    returncode: int
    session_id: str


@dataclass
class SessionInfo:
    """Session metadata."""
    session_id: str
    host: str
    user: str
    port: int
    created_at: str
    is_active: bool


class RemctlSession:
    """
    Unified SSH Session Manager
    
    Class Methods (for multi-session):
        RemctlSession.create(host, user, password) → session_id
        RemctlSession.list() → all sessions
        RemctlSession.snapshot(session_id) → session info
        RemctlSession.execute(session_id, command) → result
        RemctlSession.close(session_id) → close
    
    Instance Methods (for single session):
        session = RemctlSession(host, user, password)
        session.connect()
        session.execute("ls -la")
        session.close()
    """
    
    # Class-level session storage (shared across all instances)
    _sessions: Dict[str, 'RemctlSession'] = {}
    _info: Dict[str, SessionInfo] = {}
    
    # Instance attributes
    def __init__(
        self,
        host: str,
        user: str,
        password: Optional[str] = None,
        pkey_str: Optional[str] = None,
        port: int = 22,
        timeout: int = 10,
        on_output: Optional[Callable[[str], None]] = None,
    ):
        self.host = host
        self.user = user
        self.password = password
        self.pkey_str = pkey_str
        self.port = port
        self.timeout = timeout
        self.on_output = on_output
        
        self.session_id = str(uuid.uuid4())[:8]
        self.token = secrets.token_urlsafe(32)
        
        self.client: Optional[paramiko.SSHClient] = None
        self.chan: Optional[paramiko.Channel] = None
        self._connected = False
        self._output_queue: Queue = Queue()
        self._reader_thread: Optional[threading.Thread] = None
        self._reading = False
        self.audit_events: List[dict] = []
    
    def _audit(self, event: str, data: str = ""):
        """Record audit event."""
        self.audit_events.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session": self.session_id,
            "event": event,
            "data": data,
        })
    
    def connect(self):
        """Establish SSH connection."""
        self._audit("CONNECT")
        
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if self.pkey_str:
            key = paramiko.RSAKey.from_private_key(io.StringIO(self.pkey_str))
            self.client.connect(
                self.host, username=self.user, pkey=key,
                port=self.port, timeout=self.timeout,
            )
        else:
            self.client.connect(
                self.host, username=self.user, password=self.password,
                port=self.port, timeout=self.timeout,
            )
        
        self.chan = self.client.invoke_shell(term="xterm")
        self.chan.settimeout(self.timeout)
        self._connected = True
        self._reading = True
        
        self._reader_thread = threading.Thread(
            target=self._reader_loop, daemon=True,
            name=f"ssh-reader-{self.session_id}",
        )
        self._reader_thread.start()
        self._audit("CONNECTED")
    
    def _reader_loop(self):
        """Background reader thread."""
        try:
            while self._reading and self.chan:
                if self.chan.recv_ready():
                    data = self.chan.recv(4096).decode(errors="ignore")
                    if data:
                        self._output_queue.put(data)
                        if self.on_output:
                            self.on_output(data)
                else:
                    time.sleep(0.01)
        except Exception as e:
            if self._reading:
                self._output_queue.put(f"\r\n[Error: {e}]\r\n")
        finally:
            self._reading = False
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected and self.chan is not None
    
    def execute(self, command: str, wait: float = 0.5) -> SessionResult:
        """Execute command."""
        if not self._connected:
            raise RuntimeError("Not connected")
        
        self._audit("CMD", command)
        
        while not self._output_queue.empty():
            try:
                self._output_queue.get_nowait()
            except Empty:
                break
        
        self.chan.send((command + "\n").encode())
        time.sleep(wait)
        
        output = []
        start = time.time()
        while time.time() - start < wait:
            try:
                data = self._output_queue.get(timeout=0.1)
                output.append(data)
            except Empty:
                break
        
        return SessionResult(
            stdout="".join(output),
            stderr="",
            returncode=0,
            session_id=self.session_id,
        )
    
    def close(self):
        """Close session."""
        self._audit("CLOSE")
        self._connected = False
        self._reading = False
        
        if self.chan:
            self.chan.close()
        if self.client:
            self.client.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, *args):
        self.close()
    
    # ============ CLASS METHODS (Multi-Session Management) ============
    
    @classmethod
    def create(
        cls,
        host: str,
        user: str,
        password: Optional[str] = None,
        pkey_str: Optional[str] = None,
        port: int = 22,
    ) -> str:
        """
        Create new SSH session.
        
        Args:
            host: Server hostname/IP
            user: Username
            password: Password (optional if using key)
            pkey_str: Private key string (optional)
            port: SSH port (default: 22)
        
        Returns:
            Session ID
        """
        session = cls(
            host=host, user=user, password=password,
            pkey_str=pkey_str, port=port,
        )
        session.connect()
        
        sid = session.session_id
        cls._sessions[sid] = session
        cls._info[sid] = SessionInfo(
            session_id=sid, host=host, user=user, port=port,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_active=True,
        )
        return sid
    
    @classmethod
    def list(cls) -> List[Dict]:
        """List all active sessions."""
        return [asdict(info) for info in cls._info.values()]
    
    @classmethod
    def snapshot(cls, session_id: str) -> Dict:
        """Get session snapshot."""
        session = cls._sessions.get(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        
        info = cls._info.get(session_id)
        return {
            "status": "success",
            "session": asdict(info) if info else {},
            "is_connected": session.is_connected(),
            "commands_executed": len(session.audit_events),
            "recent_commands": session.audit_events[-5:],
        }
    
    @classmethod
    def execute(cls, session_id: str, command: str, wait: float = 0.5) -> Dict:
        """
        Execute command in session (only session_id needed!).
        
        Args:
            session_id: Session ID (from create())
            command: Command to execute
            wait: Wait time for output (default: 0.5s)
        
        Returns:
            Command result
        """
        session = cls._sessions.get(session_id)
        if not session:
            return {
                "status": "error",
                "message": f"Session '{session_id}' not found",
                "available": list(cls._sessions.keys())
            }
        
        if not session.is_connected():
            return {"status": "error", "message": "Session not connected"}
        
        try:
            result = session.execute(command, wait)
            return {
                "status": "success",
                "session_id": session_id,
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "session_id": session_id}
    
    @classmethod
    def close(cls, session_id: str) -> bool:
        """Close session."""
        session = cls._sessions.pop(session_id, None)
        if session:
            cls._info.pop(session_id, None)
            session.close()
            return True
        return False
    
    @classmethod
    def close_all(cls):
        """Close all sessions."""
        for s in cls._sessions.values():
            s.close()
        cls._sessions.clear()
        cls._info.clear()
