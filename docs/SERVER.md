# Server MCP Module - Complete Documentation

## 🖥️ Overview

The Server module provides SSH server management through **WebSocket** and **MCP tools** with shared session state. Built for real-time server operations with token-based security.

## 🏗️ Module Structure

```
modules/server/
├── config/                    # Configuration & Session Management
│   ├── ssh_session.py        # SSH session with token generation
│   └── websocket_handler.py  # WebSocket real-time handler
├── tools/                     # MCP Tools Implementation
│   ├── server.py             # Core operations (25+ tools)
│   └── server_tools.py       # MCP tool registration
└── routes/                    # FastAPI Routes
    └── server.py             # REST API & WebSocket endpoints
```

## 🎯 Key Features

- 🔐 **Token Authentication** - Secure token per WebSocket session
- 🌐 **WebSocket Support** - Real-time bidirectional communication
- 🛠️ **25+ MCP Tools** - Comprehensive server operations
- ✅ **Command Confirmation** - Safety for dangerous operations
- 📊 **Session Management** - Multi-session with isolation
- 🔄 **State Consistency** - Shared state between WebSocket and MCP

## 🚀 Architecture Flow

```
┌──────────────────────────────────────────────────────────────┐
│                     SESSION LIFECYCLE                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Client → WebSocket Connect                               │
│     ws://localhost:8017/server/ws                            │
│                                                              │
│  2. Client → SSH Connection Request                          │
│     {"type": "connect", "host": "...", "user": "...", ...}   │
│                                                              │
│  3. Server → SSH Session Created                             │
│     - Establish SSH connection                               │
│     - Generate unique token (32-byte URL-safe)               │
│     - Map token to session                                   │
│                                                              │
│  4. Server → Send Token to Client                            │
│     {"type": "connected", "token": "...", "session_id": ...} │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  SESSION ACTIVE - DUAL ACCESS:                         │ │
│  │                                                        │ │
│  │  A) WebSocket (Real-time Interactive)                 │ │
│  │     - Execute commands with confirmation              │ │
│  │     - Live output streaming                           │ │
│  │     - Interactive input/output                        │ │
│  │     - Command: ws.send({"type": "execute", ...})      │ │
│  │                                                        │ │
│  │  B) MCP Tools (Token-based REST API)                  │ │
│  │     - Execute tools in same SSH session               │ │
│  │     - No confirmation needed                          │ │
│  │     - Token in header: X-MCP-Token                    │ │
│  │     - Endpoint: POST /server/mcp/execute              │ │
│  │                                                        │ │
│  │  ⚡ SHARED STATE:                                      │ │
│  │     - Same SSH connection                             │ │
│  │     - Same working directory                          │ │
│  │     - Same environment variables                      │ │
│  │     - Same session history                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  5. Client → Disconnect                                      │
│     {"type": "disconnect"}                                   │
│                                                              │
│  6. Server → Cleanup                                         │
│     - Close SSH connection                                   │
│     - Invalidate token                                       │
│     - Remove session from mapping                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 🎯 Quick Start

### 1. Import and Setup

```python
from src.modules.server.tools import register_server_tools
from src.modules.server.routes import router
from src.modules.server.config import SSHSession, ServerWebSocketHandler

# Register MCP tools
register_server_tools(mcp)

# Add FastAPI routes
app.include_router(router)
```

### 2. Start Server

```bash
# Start MCP server
python -m src.server run_sse

# Server runs on http://localhost:8017
# WebSocket: ws://localhost:8017/server/ws
# REST API: http://localhost:8017/server/*
```

### 3. Connect via WebSocket

```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8017/server/ws"
    websocket = await websockets.connect(uri)
    
    # Send SSH connection request
    await websocket.send(json.dumps({
        "type": "connect",
        "host": "example.com",
        "user": "admin",
        "password": "secret",
        "port": 22
    }))
    
    # Receive token
    response = json.loads(await websocket.recv())
    token = response["token"]
    session_id = response["session_id"]
    
    print(f"Connected! Token: {token[:20]}...")
    return websocket, token

asyncio.run(connect())
```

### 4. Use MCP Tools with Token

```python
import requests

# Use token from WebSocket connection
headers = {"X-MCP-Token": token}

# Execute command via MCP
response = requests.post(
    "http://localhost:8017/server/mcp/execute",
    headers=headers,
    json={"command": "whoami"}
)

print(response.json()["stdout"])
```

---

## 📚 Available MCP Tools (25+)

### Basic Info Tools (4)

| Tool | Description | Example |
|------|-------------|---------|
| `server_whoami` | Get current user | `whoami` |
| `server_hostname` | Get server hostname | `hostname` |
| `server_uname` | Get system info | `uname -a` |
| `server_uptime` | Get system uptime | `uptime` |

### File Operations (8)

| Tool | Description | Example |
|------|-------------|---------|
| `server_ls` | List directory contents | `ls /home/user` |
| `server_cat` | Read file content | `cat config.txt` |
| `server_pwd` | Print working directory | `pwd` |
| `server_cd` | Change directory | `cd /var/log` |
| `server_mkdir` | Create directory | `mkdir new_folder` |
| `server_rm` | Remove file/directory | `rm -rf temp` |
| `server_cp` | Copy file/directory | `cp file.txt backup.txt` |
| `server_mv` | Move/rename file | `mv old.txt new.txt` |

### Search Tools (3)

| Tool | Description | Example |
|------|-------------|---------|
| `server_find` | Search files | `find /home -name "*.log"` |
| `server_grep` | Search in files | `grep "error" /var/log/app.log` |
| `server_which` | Find executable path | `which python3` |

### System Monitoring (5)

| Tool | Description | Example |
|------|-------------|---------|
| `server_ps` | List processes | `ps aux` |
| `server_top` | Process monitor (snapshot) | `top -n 1` |
| `server_df` | Disk space usage | `df -h` |
| `server_du` | Directory size | `du -sh /var/log` |
| `server_free` | Memory usage | `free -m` |

### Process Management (2)

| Tool | Description | Example |
|------|-------------|---------|
| `server_kill` | Kill process | `kill -9 1234` |
| `server_killall` | Kill by name | `killall python3` |

### Service Management (3)

| Tool | Description | Example |
|------|-------------|---------|
| `server_systemctl` | Manage systemd services | `systemctl status nginx` |
| `server_service` | Manage SysV services | `service apache2 restart` |
| `server_journalctl` | View systemd logs | `journalctl -u nginx` |

---

## 💡 Usage Examples

### Example 1: System Health Check

```python
import requests

# Get token from WebSocket connection
token = "your_session_token"
headers = {"X-MCP-Token": token}
base_url = "http://localhost:8017/server/mcp"

# Check system info
response = requests.post(f"{base_url}/execute", 
    headers=headers,
    json={"command": "uname -a"})
print("System:", response.json()["stdout"])

# Check uptime
response = requests.post(f"{base_url}/execute",
    headers=headers, 
    json={"command": "uptime"})
print("Uptime:", response.json()["stdout"])

# Check disk space
response = requests.post(f"{base_url}/execute",
    headers=headers,
    json={"command": "df -h"})
print("Disk Usage:\n", response.json()["stdout"])

# Check memory
response = requests.post(f"{base_url}/execute",
    headers=headers,
    json={"command": "free -m"})
print("Memory:\n", response.json()["stdout"])
```

### Example 2: Log Analysis

```python
# Find error logs in last 100 lines
response = requests.post(f"{base_url}/execute",
    headers=headers,
    json={"command": "tail -n 100 /var/log/app.log | grep -i error"})

errors = response.json()["stdout"]
print(f"Found {len(errors.splitlines())} errors:")
print(errors)

# Search for specific error pattern
response = requests.post(f"{base_url}/execute",
    headers=headers,
    json={"command": 'grep -r "connection refused" /var/log/'})

print("Connection errors:", response.json()["stdout"])
```

### Example 3: Service Management

```python
# Check service status
response = requests.post(f"{base_url}/execute",
    headers=headers,
    json={"command": "systemctl status nginx"})

status = response.json()["stdout"]
if "active (running)" in status:
    print("✅ Nginx is running")
else:
    print("❌ Nginx is down")
    
    # Restart service (requires confirmation via WebSocket)
    await websocket.send(json.dumps({
        "type": "execute",
        "command": "systemctl restart nginx",
        "require_confirmation": True
    }))

# View recent logs
response = requests.post(f"{base_url}/execute",
    headers=headers,
    json={"command": "journalctl -u nginx -n 50 --no-pager"})

print("Recent logs:", response.json()["stdout"])
```

### Example 4: File Management Pipeline

```python
# Create backup directory
requests.post(f"{base_url}/execute",
    headers=headers,
    json={"command": "mkdir -p /home/user/backups"})

# Find and copy config files
requests.post(f"{base_url}/execute",
    headers=headers,
    json={"command": 'find /etc/myapp -name "*.conf" -exec cp {} /home/user/backups/ \\;'})

# Verify backup
response = requests.post(f"{base_url}/execute",
    headers=headers,
    json={"command": "ls -lh /home/user/backups"})

print("Backed up files:", response.json()["stdout"])

# Create archive
requests.post(f"{base_url}/execute",
    headers=headers,
    json={"command": "tar -czf /home/user/config-backup.tar.gz /home/user/backups"})

print("✅ Backup complete: config-backup.tar.gz")
```

---

## 🔧 Advanced Features

### 1. WebSocket vs MCP Tools

**WebSocket (Interactive Mode):**
- Real-time output streaming
- Command confirmation for dangerous operations
- Interactive terminal experience
- Best for: manual debugging, live monitoring

**MCP Tools (Automated Mode):**
- Token-based programmatic access
- No confirmation needed
- Structured JSON responses
- Best for: automation, scripts, workflows

### 2. Session Management

```python
from src.modules.server.config import SSHSession

# Create SSH session
session = SSHSession(
    host="example.com",
    user="admin",
    password="secret",
    port=22
)

# Generate secure token
token = session.generate_token()

# Store in global mapping
sessions[token] = session

# Retrieve session later
session = sessions.get(token)

# Execute command
stdout, stderr, return_code = session.execute_command("ls -la")

# Cleanup
session.close()
del sessions[token]
```

### 3. Command Confirmation System

Commands requiring confirmation (via WebSocket):
- `rm`, `rmdir` - File/directory deletion
- `kill`, `killall` - Process termination  
- `systemctl stop/restart` - Service control
- `reboot`, `shutdown` - System power

MCP tools skip confirmation for automation.

### 4. Error Handling

```python
try:
    response = requests.post(f"{base_url}/execute",
        headers=headers,
        json={"command": "invalid_command"},
        timeout=30)
    
    data = response.json()
    
    if data.get("return_code") != 0:
        print(f"Command failed: {data['stderr']}")
    else:
        print(f"Success: {data['stdout']}")
        
except requests.exceptions.Timeout:
    print("Command timed out")
except requests.exceptions.ConnectionError:
    print("Cannot connect to server")
except Exception as e:
    print(f"Error: {e}")
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# .env file
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8017
SSH_TIMEOUT=30
MAX_SESSIONS=100
TOKEN_EXPIRY=3600  # 1 hour
```

### Session Limits

```python
# config/ssh_session.py
MAX_CONCURRENT_SESSIONS = 100
SESSION_TIMEOUT = 3600  # seconds
TOKEN_LENGTH = 32  # bytes
```

### WebSocket Settings

```python
# routes/server.py
WEBSOCKET_TIMEOUT = 300  # 5 minutes
PING_INTERVAL = 30  # seconds
MAX_MESSAGE_SIZE = 10_485_760  # 10MB
```

---

## 🔐 Best Practices

### 1. Secure Token Management

```python
import os
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self):
        self.tokens = {}
        
    def create_token(self, session):
        token = os.urandom(32).hex()
        self.tokens[token] = {
            "session": session,
            "created": datetime.now(),
            "expires": datetime.now() + timedelta(hours=1)
        }
        return token
        
    def validate_token(self, token):
        if token not in self.tokens:
            return None
            
        data = self.tokens[token]
        if datetime.now() > data["expires"]:
            del self.tokens[token]
            return None
            
        return data["session"]
        
    def revoke_token(self, token):
        if token in self.tokens:
            del self.tokens[token]
```

### 2. Command Validation

```python
DANGEROUS_COMMANDS = [
    "rm -rf /",
    "mkfs",
    "dd if=/dev/zero",
    "> /dev/sda"
]

def validate_command(command: str) -> bool:
    """Prevent dangerous commands"""
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in command:
            raise ValueError(f"Dangerous command blocked: {dangerous}")
    return True
```

### 3. Resource Cleanup

```python
import atexit

def cleanup_sessions():
    """Close all sessions on server shutdown"""
    for token, session in sessions.copy().items():
        try:
            session.close()
            del sessions[token]
        except:
            pass

atexit.register(cleanup_sessions)
```

### 4. Logging and Monitoring

```python
import logging

logger = logging.getLogger("server_mcp")

def execute_with_logging(session, command):
    logger.info(f"Executing: {command}")
    
    try:
        stdout, stderr, code = session.execute_command(command)
        logger.info(f"Success: return_code={code}")
        return stdout, stderr, code
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise
```

---

## 🧪 Testing

### Unit Tests

```python
import pytest
from src.modules.server.config import SSHSession

def test_ssh_session_creation():
    session = SSHSession(
        host="localhost",
        user="test",
        password="test"
    )
    
    assert session.host == "localhost"
    assert session.user == "test"
    
def test_token_generation():
    session = SSHSession("localhost", "test", "test")
    token = session.generate_token()
    
    assert len(token) == 64  # 32 bytes hex = 64 chars
    assert isinstance(token, str)

def test_command_execution():
    session = SSHSession("localhost", "test", "test")
    stdout, stderr, code = session.execute_command("echo hello")
    
    assert stdout.strip() == "hello"
    assert code == 0
```

### Integration Tests

```python
import asyncio
import websockets
import pytest

@pytest.mark.asyncio
async def test_websocket_session_flow():
    uri = "ws://localhost:8017/server/ws"
    
    async with websockets.connect(uri) as ws:
        # Connect
        await ws.send(json.dumps({
            "type": "connect",
            "host": "localhost",
            "user": "test",
            "password": "test"
        }))
        
        # Get token
        response = json.loads(await ws.recv())
        assert response["type"] == "connected"
        assert "token" in response
        
        token = response["token"]
        
        # Execute command
        await ws.send(json.dumps({
            "type": "execute",
            "command": "whoami"
        }))
        
        # Get result
        result = json.loads(await ws.recv())
        assert result["return_code"] == 0
        assert len(result["stdout"]) > 0
        
        # Disconnect
        await ws.send(json.dumps({"type": "disconnect"}))

@pytest.mark.asyncio  
async def test_mcp_tool_with_token():
    # First get token via WebSocket
    async with websockets.connect("ws://localhost:8017/server/ws") as ws:
        await ws.send(json.dumps({
            "type": "connect",
            "host": "localhost",
            "user": "test",
            "password": "test"
        }))
        
        response = json.loads(await ws.recv())
        token = response["token"]
    
    # Use token with MCP tool
    import requests
    response = requests.post(
        "http://localhost:8017/server/mcp/execute",
        headers={"X-MCP-Token": token},
        json={"command": "ls -la"}
    )
    
    assert response.status_code == 200
    assert "stdout" in response.json()
```

---

## 📖 API Reference

### WebSocket Messages

**Connect:**
```json
{
  "type": "connect",
  "host": "example.com",
  "user": "admin",
  "password": "secret",
  "port": 22
}
```

**Execute:**
```json
{
  "type": "execute",
  "command": "ls -la",
  "require_confirmation": false
}
```

**Confirm:**
```json
{
  "type": "confirm",
  "confirmed": true
}
```

**Disconnect:**
```json
{
  "type": "disconnect"
}
```

### REST API Endpoints

**POST /server/mcp/execute**
```python
# Headers
{"X-MCP-Token": "your_token_here"}

# Body
{"command": "whoami"}

# Response
{
  "stdout": "admin\n",
  "stderr": "",
  "return_code": 0
}
```

---

## 🔗 Related Documentation

- [Main README](../README.md) - Project overview and quick start
- [Excel Module](EXCEL.md) - Excel MCP tools documentation
- [FastMCP Documentation](https://github.com/jlowin/fastmcp) - MCP framework
- [Paramiko Documentation](https://www.paramiko.org/) - SSH library

---

## 🆘 Troubleshooting

### Issue 1: WebSocket Connection Failed

**Symptoms:** Cannot connect to `ws://localhost:8017/server/ws`

**Solutions:**
```bash
# Check if server is running
curl http://localhost:8017/health

# Check port availability
netstat -ano | findstr 8017

# Restart server
python -m src.server run_sse
```

### Issue 2: SSH Authentication Failed

**Symptoms:** `{"type": "error", "message": "Authentication failed"}`

**Solutions:**
```python
# Try different auth methods
await ws.send(json.dumps({
    "type": "connect",
    "host": "example.com",
    "user": "admin",
    # Option 1: Password
    "password": "secret",
    # Option 2: SSH Key
    "key_filename": "/path/to/key.pem"
}))

# Check SSH connectivity manually
ssh admin@example.com
```

### Issue 3: Token Invalid or Expired

**Symptoms:** `401 Unauthorized` from MCP endpoint

**Solutions:**
```python
# Tokens expire after 1 hour - reconnect
async with websockets.connect(uri) as ws:
    await ws.send(json.dumps({"type": "connect", ...}))
    response = json.loads(await ws.recv())
    new_token = response["token"]

# Check token exists in session
print(f"Active sessions: {len(sessions)}")
```

### Issue 4: Command Timeout

**Symptoms:** Long-running command never returns

**Solutions:**
```python
# Increase timeout
response = requests.post(
    f"{base_url}/execute",
    headers=headers,
    json={"command": "long_running_task"},
    timeout=300  # 5 minutes
)

# Use background task for very long commands
await ws.send(json.dumps({
    "type": "execute",
    "command": "nohup long_task.sh &"
}))
```

---

## 📝 Changelog

### v2.0.0 - Modular Architecture
- ✨ Restructured to `modules/server/` architecture
- 🔧 Separated config, tools, and routes
- 📚 Enhanced documentation with examples
- 🐛 Fixed import paths

### v1.0.0 - Initial Release
- 🎉 WebSocket + MCP tools integration  
- 🔐 Token-based session management
- 🛠️ 25+ server operation tools
- ✅ Command confirmation system

---

**Last Updated:** 2024-01
**Module Version:** 2.0.0
**License:** MIT
        "port": 22
    }))
    
    # Receive connected message with TOKEN
    response = await websocket.recv()
    data = json.loads(response)
    
    print(f"✅ Session Created!")
    print(f"   Session ID: {data['session_id']}")
    print(f"   Token: {data['token']}")  # ← IMPORTANT: Save this token
    print(f"   Host: {data['host']}")
    
    return websocket, data['token']

# Run
websocket, token = asyncio.run(create_session())
```

**Response:**
```json
{
  "type": "connected",
  "session_id": "a1b2c3d4",
  "token": "AbCd123XyZ456_your_mcp_token_32chars",
  "host": "example.com",
  "user": "admin"
}
```

**🔑 SAVE THIS TOKEN!** Token ini yang akan digunakan untuk akses MCP tools.

---

### Step 3A: Use WebSocket (Interactive)

WebSocket untuk **interactive terminal** dan **real-time streaming**:

```python
async def use_websocket(websocket):
    """Execute commands via WebSocket with confirmation."""
    
    # Execute command (requires confirmation by default)
    await websocket.send(json.dumps({
        "type": "execute",
        "command": "ls -la"
    }))
    
    # Receive confirmation request
    response = await websocket.recv()
    confirm = json.loads(response)
    
    if confirm["type"] == "confirm_required":
        print(f"Confirm: {confirm['command']}")
        
        # Send approval
        await websocket.send(json.dumps({
            "type": "confirm_execute",
            "confirm_id": confirm["confirm_id"],
            "approved": True
        }))
        
        # Receive result
        response = await websocket.recv()
        result = json.loads(response)
        print(f"Output: {result['stdout']}")
```

**Features:**
- ✅ Real-time output streaming
- ✅ Interactive command execution
- ✅ Command confirmation for security
- ✅ Live session management

---

### Step 3B: Use MCP Tools (With Token)

MCP tools menggunakan **token dari WebSocket** untuk akses session yang sama:

```python
import requests

# Token from Step 2
TOKEN = "AbCd123XyZ456_your_mcp_token_32chars"

def use_mcp_tools(token):
    """Execute MCP tools using token from WebSocket."""
    
    headers = {"X-MCP-Token": token}
    
    # Tool 1: whoami
    response = requests.post(
        "http://localhost:8017/server/mcp/execute",
        headers=headers,
        json={"command": "whoami"}
    )
    print(f"Current user: {response.json()['stdout']}")
    
    # Tool 2: pwd
    response = requests.post(
        "http://localhost:8017/server/mcp/execute",
        headers=headers,
        json={"command": "pwd"}
    )
    print(f"Current dir: {response.json()['stdout']}")
    
    # Tool 3: ls -la
    response = requests.post(
        "http://localhost:8017/server/mcp/execute",
        headers=headers,
        json={"command": "ls -la"}
    )
    print(f"Files:\n{response.json()['stdout']}")

# Use the same session via MCP
use_mcp_tools(TOKEN)
```

**Features:**
- ✅ REST API access ke session yang sama
- ✅ 25+ built-in tools (whoami, ls, find, grep, etc.)
- ✅ Token-based authentication
- ✅ Session state tetap konsisten dengan WebSocket

---

### Step 4: Combined Usage (WebSocket + MCP Together)

**Best Practice:** Gunakan keduanya secara bersamaan:

```python
import asyncio
import websockets
import requests
import json

async def combined_usage():
    """Demonstrate WebSocket + MCP tools in same session."""
    
    uri = "ws://localhost:8017/server/ws"
    
    async with websockets.connect(uri) as ws:
        # ============ 1. CREATE SESSION ============
        print("📡 Creating session...")
        await ws.send(json.dumps({
            "type": "connect",
            "host": "example.com",
            "user": "admin",
            "password": "secret"
        }))
        
        response = await ws.recv()
        data = json.loads(response)
        token = data['token']
        session_id = data['session_id']
        
        print(f"✅ Session created: {session_id}")
        print(f"🔑 Token: {token[:20]}...\n")
        
        # ============ 2. USE WEBSOCKET ============
        print("🌐 Using WebSocket...")
        
        # Change directory via WebSocket
        await ws.send(json.dumps({
            "type": "execute",
            "command": "cd /var/log",
            "skip_confirm": True
        }))
        
        # Wait for confirmation
        response = await ws.recv()
        if json.loads(response)["type"] == "result":
            print("   ✅ Changed directory via WebSocket")
        
        # ============ 3. USE MCP TOOLS ============
        print("\n🛠️  Using MCP Tools (same session)...")
        
        headers = {"X-MCP-Token": token}
        
        # Check current directory (should be /var/log from step 2)
        response = requests.post(
            "http://localhost:8017/server/mcp/execute",
            headers=headers,
            json={"command": "pwd"}
        )
        current_dir = response.json()['stdout'].strip()
        print(f"   📁 Current dir from MCP: {current_dir}")
        
        # List files using MCP
        response = requests.post(
            "http://localhost:8017/server/mcp/execute",
            headers=headers,
            json={"command": "ls -la"}
        )
        files = response.json()['stdout']
        print(f"   📄 Files from MCP:\n{files[:200]}...")
        
        # ============ 4. BACK TO WEBSOCKET ============
        print("\n🌐 Back to WebSocket...")
        
        # Execute another command via WebSocket
        await ws.send(json.dumps({
            "type": "execute",
            "command": "uptime",
            "skip_confirm": True
        }))
        
        response = await ws.recv()
        if json.loads(response)["type"] == "result":
            uptime = json.loads(response)['stdout']
            print(f"   ⏰ Uptime: {uptime.strip()}")
        
        # ============ 5. VALIDATE SESSION ============
        print("\n🔍 Validating session...")
        
        response = requests.get(
            "http://localhost:8017/server/mcp/validate",
            headers=headers
        )
        print(f"   ✅ Token valid: {response.json()['valid']}")
        print(f"   📊 Session info: {response.json()}")
        
        # ============ 6. DISCONNECT ============
        print("\n👋 Disconnecting...")
        await ws.send(json.dumps({"type": "disconnect"}))
        await ws.recv()
        
        print("   ✅ Session closed")
        print("   ⚠️  Token is now invalid")

asyncio.run(combined_usage())
```

**Output:**
```
📡 Creating session...
✅ Session created: a1b2c3d4
🔑 Token: AbCd123XyZ456_your_m...

🌐 Using WebSocket...
   ✅ Changed directory via WebSocket

🛠️  Using MCP Tools (same session)...
   📁 Current dir from MCP: /var/log
   📄 Files from MCP:
   total 1234
   drwxr-xr-x  2 root root 4096 Jan 17 10:00 .
   ...

🌐 Back to WebSocket...
   ⏰ Uptime: 10:45:23 up 5 days, 12:34, 1 user

🔍 Validating session...
   ✅ Token valid: true
   📊 Session info: {'valid': True, 'session_id': 'a1b2c3d4', ...}

👋 Disconnecting...
   ✅ Session closed
   ⚠️  Token is now invalid
```

---

## 🔄 Session State Consistency

**PENTING:** WebSocket dan MCP tools berbagi **STATE yang SAMA**:

```python
# 1. Change directory via WebSocket
await ws.send({"type": "execute", "command": "cd /var/log"})

# 2. Check directory via MCP (same session!)
response = requests.post(
    "/server/mcp/execute",
    headers={"X-MCP-Token": token},
    json={"command": "pwd"}
)
# Output: /var/log  ← State konsisten!

# 3. Create file via MCP
requests.post(
    "/server/mcp/execute",
    headers={"X-MCP-Token": token},
    json={"command": "touch test.txt"}
)

# 4. List files via WebSocket (same session!)
await ws.send({"type": "execute", "command": "ls"})
# Output: test.txt  ← File terlihat!
```

---

## 📊 Available MCP Tools (25+)

Semua tools ini bisa digunakan dengan token dari WebSocket session:

### Basic Info Tools
```python
# whoami - Current user
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "whoami"}

# pwd - Current directory
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "pwd"}

# hostname - Server hostname
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "hostname"}

# uname - System info
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "uname -a"}
```

### File Operations
```python
# ls - List directory
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "ls -la /var/log"}

# find - Find files
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "find /var/log -name '*.log'"}

# grep - Search in files
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "grep 'error' /var/log/syslog"}

# cat - Read file
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "cat /etc/hostname"}
```

### System Info
```python
# df - Disk usage
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "df -h"}

# free - Memory usage
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "free -h"}

# ps - Process list
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "ps aux"}

# uptime - System uptime
POST /server/mcp/execute
Headers: X-MCP-Token: {token}
Body: {"command": "uptime"}
```

---

## 🔒 Security: Command Confirmation

WebSocket commands require **confirmation by default**:

```python
# 1. Request command
await ws.send(json.dumps({
    "type": "execute",
    "command": "rm -rf /tmp/test"
}))

# 2. Server asks for confirmation
response = await ws.recv()
# {
#   "type": "confirm_required",
#   "confirm_id": "abc123",
#   "command": "rm -rf /tmp/test",
#   "warning": "⚠️ WARNING: This command can delete files!"
# }

# 3. User approves/declines
await ws.send(json.dumps({
    "type": "confirm_execute",
    "confirm_id": "abc123",
    "approved": True  # or False to cancel
}))

# 4. Server executes (if approved)
response = await ws.recv()
# {"type": "result", "stdout": "...", "confirmed": true}
```

**Skip confirmation** for safe commands:
```python
await ws.send(json.dumps({
    "type": "execute",
    "command": "whoami",
    "skip_confirm": True  # ← No confirmation
}))
```

---

## 🚀 Quick Start Examples

### Example 1: Simple Session

```python
import asyncio
import websockets
import requests
import json

async def simple_example():
    uri = "ws://localhost:8017/server/ws"
    
    async with websockets.connect(uri) as ws:
        # Connect
        await ws.send(json.dumps({
            "type": "connect",
            "host": "example.com",
            "user": "admin",
            "password": "secret"
        }))
        
        # Get token
        data = json.loads(await ws.recv())
        token = data['token']
        
        # Use MCP tool
        response = requests.post(
            "http://localhost:8017/server/mcp/execute",
            headers={"X-MCP-Token": token},
            json={"command": "whoami"}
        )
        print(response.json()['stdout'])
        
        # Disconnect
        await ws.send(json.dumps({"type": "disconnect"}))

asyncio.run(simple_example())
```

### Example 2: AI Agent Usage

```python
class SSHTerminalAgent:
    """AI Agent with terminal access via MCP."""
    
    def __init__(self):
        self.token = None
        self.websocket = None
    
    async def connect(self, host, user, password):
        """Establish SSH session and get token."""
        uri = "ws://localhost:8017/server/ws"
        self.websocket = await websockets.connect(uri)
        
        await self.websocket.send(json.dumps({
            "type": "connect",
            "host": host,
            "user": user,
            "password": password
        }))
        
        response = await self.websocket.recv()
        data = json.loads(response)
        self.token = data['token']
        
        return data['session_id']
    
    def execute_tool(self, command):
        """Execute command using MCP tool."""
        response = requests.post(
            "http://localhost:8017/server/mcp/execute",
            headers={"X-MCP-Token": self.token},
            json={"command": command}
        )
        return response.json()['stdout']
    
    async def execute_interactive(self, command, skip_confirm=True):
        """Execute command via WebSocket."""
        await self.websocket.send(json.dumps({
            "type": "execute",
            "command": command,
            "skip_confirm": skip_confirm
        }))
        
        response = await self.websocket.recv()
        data = json.loads(response)
        return data.get('stdout', '')
    
    async def disconnect(self):
        """Close session."""
        if self.websocket:
            await self.websocket.send(json.dumps({"type": "disconnect"}))
            await self.websocket.recv()
            self.token = None

# Usage
async def main():
    agent = SSHTerminalAgent()
    
    # Connect
    session_id = await agent.connect("example.com", "admin", "secret")
    print(f"Connected: {session_id}")
    
    # Use MCP tools
    user = agent.execute_tool("whoami")
    print(f"User: {user}")
    
    # Use WebSocket
    files = await agent.execute_interactive("ls -la")
    print(f"Files: {files}")
    
    # Disconnect
    await agent.disconnect()

asyncio.run(main())
```

---

## ❓ FAQ

### Q: Apakah WebSocket dan MCP berbagi session yang sama?
**A:** YA! WebSocket membuat session, generate token, dan MCP tools menggunakan token tersebut untuk akses session yang sama.

### Q: Apakah perubahan di WebSocket terlihat di MCP?
**A:** YA! Jika change directory di WebSocket, MCP tools juga akan berada di directory yang sama.

### Q: Apakah token expired?
**A:** Token valid selama WebSocket session aktif. Saat disconnect, token langsung invalid.

### Q: Bisa punya multiple sessions?
**A:** YA! Buat multiple WebSocket connections, masing-masing dapat token unik dan session terpisah.

### Q: MCP tools juga butuh confirmation?
**A:** TIDAK. Confirmation hanya untuk WebSocket `execute` command. MCP tools langsung execute.

### Q: Bagaimana cara mengintegrasikan dengan LangAI-Base?
**A:** Gunakan WebSocket untuk create session di awal workflow, simpan token di state, lalu MCP tools bisa akses token tersebut.

---

## 🔗 Integration with LangAI-Base

```python
# In LangAI-Base worker
async def homeserver_node(state: dict):
    """Execute command using MCP terminal."""
    
    # Get token from state (created at workflow start)
    token = state.get("terminal_token")
    
    if not token:
        # Create new session if token not exists
        # (WebSocket connection should be established at workflow start)
        raise ValueError("Terminal token not found in state")
    
    # Execute command using MCP
    command = state.get("current_task", {}).get("action", "")
    
    response = requests.post(
        "http://localhost:8017/server/mcp/execute",
        headers={"X-MCP-Token": token},
        json={"command": command}
    )
    
    result = response.json()
    
    return {
        "worker_results": state.get("worker_results", []) + [{
            "worker_id": "homeserver",
            "output": result['stdout'],
            "status": "success"
        }],
        "current_step": state.get("current_step", 0) + 1
    }
```

---

## 📚 See Also

- [Terminal Tools Reference](./TERMINAL.md#available-mcp-tools-25)
- [WebSocket Protocol](./TERMINAL.md#websocket-api)
- [Security & Confirmation](./TERMINAL.md#command-confirmation)
- [Examples](../examples/)

---

**🎉 Happy Coding!**

