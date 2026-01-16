"""
SSH Session Manager for Terminal MCP Server
"""

import io
import time
import uuid
import secrets
import threading
from dataclasses import dataclass
from queue import Queue, Empty
from typing import Optional, Set, List, Callable
import paramiko


@dataclass
class CommandResult:
    """Result of a command execution."""
    stdout: str
    stderr: str
    returncode: int
    session_id: str
    token: str


class SSHSession:
    """
    SSH Terminal Session Manager
    
    Features:
    - WebSocket-compatible async output streaming
    - Command execution with policy enforcement
    - Session audit logging
    - Multi-client support
    
    Usage:
        session = SSHSession(
            host="example.com",
            user="admin",
            password="secret"
        )
        session.connect()
        result = session.execute("ls -la")
        session.close()
    """
    
    def __init__(
        self,
        host: str,
        user: str,
        password: Optional[str] = None,
        pkey_str: Optional[str] = None,
        port: int = 22,
        timeout: int = 10,
        allowlist: Optional[Set[str]] = None,
        disallowlist: Optional[Set[str]] = None,
        on_output: Optional[Callable[[str], None]] = None,
    ):
        self.host = host
        self.user = user
        self.password = password
        self.pkey_str = pkey_str
        self.port = port
        self.timeout = timeout
        self.allowlist = set(allowlist) if allowlist else None
        self.disallowlist = set(disallowlist) if disallowlist else set()
        self.on_output = on_output  # Callback for WebSocket streaming
        
        self.session_id = str(uuid.uuid4())[:8]
        self.token = secrets.token_urlsafe(32)  # MCP access token
        
        # Connection handles
        self.client: Optional[paramiko.SSHClient] = None
        self.chan: Optional[paramiko.Channel] = None
        
        self._connected = False
        self._output_queue: Queue = Queue()
        self._reader_thread: Optional[threading.Thread] = None
        self._reading = False
        
        self.audit_events: List[dict] = []
    
    # ---------- AUDIT ----------
    def _audit(self, event: str, data: str = ""):
        """Record an audit event."""
        self.audit_events.append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "session": self.session_id,
            "user": self.user,
            "host": self.host,
            "event": event,
            "data": data,
        })
    
    # ---------- CONNECT ----------
    def connect(self):
        """Establish SSH connection."""
        self._audit("CONNECT")
        
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if self.pkey_str:
                key = paramiko.RSAKey.from_private_key(io.StringIO(self.pkey_str))
                self.client.connect(
                    self.host,
                    username=self.user,
                    pkey=key,
                    port=self.port,
                    timeout=self.timeout,
                )
            else:
                self.client.connect(
                    self.host,
                    username=self.user,
                    password=self.password,
                    port=self.port,
                    timeout=self.timeout,
                )
            
            self.chan = self.client.invoke_shell(term="xterm")
            self.chan.settimeout(self.timeout)
            
            self._connected = True
            self._reading = True
            
            # Start background reader for streaming output
            self._reader_thread = threading.Thread(
                target=self._reader_loop,
                daemon=True,
                name=f"ssh-reader-{self.session_id}",
            )
            self._reader_thread.start()
            
            self._audit("CONNECTED")
            return True
            
        except Exception as e:
            self._audit("CONNECT_ERROR", str(e))
            raise
    
    def _reader_loop(self):
        """Background thread to read SSH output."""
        try:
            while self._reading and self.chan:
                if self.chan.recv_ready():
                    data = self.chan.recv(4096).decode(errors="ignore")
                    if data:
                        self._output_queue.put(data)
                        # Stream to WebSocket if callback provided
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
        """Check if session is connected."""
        return self._connected and self.chan is not None
    
    # ---------- POLICY ----------
    def _check_policy(self, cmd: str):
        """Check if command is allowed by policy."""
        base = cmd.strip().split()[0] if cmd.strip() else ""
        if not base:
            return
        if base in self.disallowlist:
            raise PermissionError(f"Command '{base}' is disallowed")
        if self.allowlist is not None and base not in self.allowlist:
            raise PermissionError(f"Command '{base}' is not in allowlist")
    
    # ---------- EXECUTE ----------
    def execute(self, command: str, wait: float = 0.5) -> CommandResult:
        """
        Execute a command in the SSH session.
        
        Args:
            command: Command string, e.g. "ls -l"
            wait: Time to wait for output
            
        Returns:
            CommandResult with stdout, stderr, and returncode
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")
        
        self._check_policy(command)
        self._audit("CMD", command)
        
        # Clear output queue
        while not self._output_queue.empty():
            try:
                self._output_queue.get_nowait()
            except Empty:
                break
        
        # Send command
        self.chan.send((command + "\n").encode())
        time.sleep(wait)
        
        # Collect output
        output = []
        start = time.time()
        while time.time() - start < wait:
            try:
                data = self._output_queue.get(timeout=0.1)
                output.append(data)
            except Empty:
                break
        
        stdout = "".join(output)
        
        return CommandResult(
            stdout=stdout,
            stderr="",
            returncode=0,
            session_id=self.session_id,
            token=self.token,
        )
    
    def send_input(self, data: str):
        """Send input to terminal (for interactive mode)."""
        if not self._connected:
            raise RuntimeError("Not connected")
        
        self._audit("INPUT", data[:50])  # Log first 50 chars
        self.chan.send(data.encode())
    
    def read_output(self, timeout: float = 0.1) -> str:
        """Read available output from terminal."""
        output = []
        start = time.time()
        while time.time() - start < timeout:
            try:
                data = self._output_queue.get(timeout=0.05)
                output.append(data)
            except Empty:
                break
        return "".join(output)
    
    # ---------- CLOSE ----------
    def close(self):
        """Close the SSH session."""
        self._audit("CLOSE")
        self._connected = False
        self._reading = False
        
        if self.chan:
            self.chan.close()
            self.chan = None
        if self.client:
            self.client.close()
            self.client = None
    
    def get_audit(self) -> List[dict]:
        """Get all audit events."""
        return self.audit_events
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
