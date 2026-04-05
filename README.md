<p align="center">
  <img src="https://raw.githubusercontent.com/haris-musa/excel-mcp-server/main/assets/logo.png" alt="MCP Server Logo" width="300"/>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# MCP Server - Modular Architecture

A **Model Context Protocol (MCP)** server with modular architecture supporting:
- 🖥️ **SSH Server Management (Remctl)** - Remote server operations via WebSocket + MCP tools with approval system
- 🗄️ **Database Management** - Multi-database operations (PostgreSQL, MySQL, SQLite, MSSQL, Oracle) with approval system

## 🏗️ Architecture Overview

```
src/
├── routes/                        # Central route registration
│   ├── remctl.py                 # Remctl WebSocket + MCP routes
│   └── database.py               # Database WebSocket + MCP routes
├── modules/
│   ├── remctl/                   # 🖥️ Remote Control Module
│   │   ├── config/               # Session management & tools registry
│   │   ├── tools/                # MCP tools (core, filesystem, system)
│   │   └── skills/               # Skill documentation (markdown files)
│   ├── database/                 # 🗄️ Database Module
│   │   ├── config/               # Connection management & tools registry
│   │   ├── tools/                # MCP tools (core, schema, admin)
│   │   └── skills/               # Skill documentation (markdown files)
│   └── approval/                 # 🔐 Command approval system
│       └── manager.py            # User approval management
└── server.py                     # Main entry point
```

### Modular Design Benefits

- ✅ **Independent Modules** - Remctl and Database operate independently
- ✅ **Approval System** - All AI actions require user approval before execution
- ✅ **Scalable** - Easy to add new modules (storage, APIs, etc.)
- ✅ **Maintainable** - Changes isolated to specific modules
- ✅ **Reusable** - Modules can import from each other
- ✅ **Clean Separation** - Routes in `src/routes/`, logic in `src/modules/`

## 🔐 Security Model

### User vs AI Roles

**User (via WebSocket):**
- ✅ Creates sessions with credentials
- ✅ Receives approval requests
- ✅ Approves/rejects AI actions
- ✅ Full control over what AI can do

**AI (via MCP Tools):**
- ✅ Uses existing sessions (cannot create new ones)
- ❌ Cannot access credentials
- ✅ Must request approval for dangerous operations
- ✅ Read-only tools don't need approval

### Approval Flow

```
AI calls tool → Server creates approval request → User receives notification
     ↓
User approves/rejects → Server executes (or cancels) → AI gets result
```

## 🖥️ Module 1: Remctl (Server Management)

### Features

- 🔐 **Token Authentication** - Secure token-based access
- 🌐 **WebSocket Support** - Real-time bidirectional communication
- 🛠️ **29+ MCP Tools** - Comprehensive server operations
- ✅ **User Approval System** - All actions require user approval
- 📚 **Skill Documentation** - AI can learn available capabilities
- 📊 **Session Management** - Multi-session support

### Architecture Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. User → WebSocket Connect (SSH credentials)          │
│     ↓                                                    │
│  2. SSH Session Created + Token Generated               │
│     ↓                                                    │
│  ┌──────────────────────────────────────────────┐      │
│  │  DUAL ACCESS (Same Session):                 │      │
│  │                                               │      │
│  │  A) WebSocket (User - Interactive)           │      │
│  │     - Real-time commands                     │      │
│  │     - Approve/reject AI requests             │      │
│  │                                               │      │
│  │  B) MCP Tools (AI - Programmatic)            │      │
│  │     - REST API with token                    │      │
│  │     - Requires user approval first           │      │
│  └──────────────────────────────────────────────┘      │
│     ↓                                                    │
│  3. WebSocket Disconnect = Token Invalid                │
└─────────────────────────────────────────────────────────┘
```

### Available Tools (29+)

| Category | Tools | Count |
|----------|-------|-------|
| **Core** | server_exec (SSH command execution) | 1 |
| **Filesystem** | server_ls, server_pwd, server_cd, server_mkdir, server_rm, server_cp, server_mv, server_cat, server_head, server_tail, server_file_info, server_find, server_grep | 13 |
| **System** | server_whoami, server_hostname, server_uname, server_uptime, server_ps, server_top, server_df, server_free, server_du, server_network, server_ping, server_kill, server_killall, systemctl, server_logs | 15 |

📖 **[Complete Remctl Documentation →](docs/SERVER.md)**

## 🗄️ Module 2: Database

### Features

- 🌐 **Multi-Database Support** - PostgreSQL, MySQL, SQLite, MSSQL, Oracle
- 🔐 **Token Authentication** - Secure token-based access
- 🌐 **WebSocket Support** - Real-time bidirectional communication
- 🛠️ **33+ MCP Tools** - Comprehensive database operations
- ✅ **User Approval System** - All write operations require approval
- 📚 **Skill Documentation** - AI can learn database patterns
- 📊 **Connection Pooling** - Multiple concurrent connections

### Available Tools (33+)

| Category | Tools | Count |
|----------|-------|-------|
| **Query** | db_query, db_query_single, db_query_count, db_insert, db_update, db_delete | 6 |
| **Schema (Read-Only, No Approval)** | db_tables, db_schema, db_columns, db_primary_key, db_foreign_keys, db_indexes, db_relationships, db_table_stats, db_column_types, db_search_tables | 10 |
| **Transaction** | db_transaction_start, db_transaction_commit, db_transaction_rollback | 3 |
| **Admin** | db_create_table, db_drop_table, db_add_column, db_drop_column, db_alter_column, db_create_index, db_drop_index, db_create_view, db_drop_view, db_truncate_table, db_rename_table, db_add_foreign_key | 12 |
| **Utility** | db_clear_cache | 1 |

### Supported Databases

- ✅ **PostgreSQL** (port 5432)
- ✅ **MySQL** (port 3306)
- ✅ **SQLite** (file or in-memory)
- ✅ **Microsoft SQL Server** (port 1433)
- ✅ **Oracle** (port 1521)

📖 **[Complete Database Documentation →](docs/DATABASE.md)**

## 🚀 Installation & Usage

### Prerequisites

```bash
pip install -r requirements.txt
```

### Running the Server

```bash
# Start server with all modules
cd MCP-Server
python -m src.server

# Server runs on http://localhost:8017
# Endpoints:
#   Remctl:   ws://localhost:8017/remctl/ws   +   http://localhost:8017/remctl/mcp
#   Database: ws://localhost:8017/database/ws +   http://localhost:8017/database/mcp
```

### Using with Claude Desktop

```json
{
  "mcpServers": {
    "remctl": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/MCP-Server",
      "env": {
        "FASTMCP_PORT": "8017"
      }
    }
  }
}
```

## 📚 Skill System

Both modules support a **Skill System** that allows AI to discover and learn available capabilities:

### How It Works

1. AI calls `get_skills()` → Gets list of available skills
2. AI calls `load_skill(skill_name)` → Loads markdown documentation
3. AI learns how to use tools properly with best practices

### Available Skills

**Remctl:**
- `server-connect` - SSH connection management
- `server-fileops` - File operations on remote servers
- `server-monitor` - Server health monitoring

**Database:**
- `database-connect` - Database connection management
- `database-query` - Query and schema exploration
- `database-admin` - Database administration tasks

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTMCP_HOST` | Server host | `0.0.0.0` |
| `FASTMCP_PORT` | Server port | `8017` |

### Transport Methods

1. **SSE** (Server-Sent Events) - Default
   ```bash
   python -m src.server
   ```

2. **WebSocket** - Real-time interactive
   - Remctl: `ws://localhost:8017/remctl/ws`
   - Database: `ws://localhost:8017/database/ws`

## 📦 Module Integration Example

### Scenario: User Connects Database, AI Queries

```python
import asyncio
import websockets
import json

async def workflow():
    # 1. User connects via WebSocket
    ws = await websockets.connect("ws://localhost:8017/database/ws")
    
    await ws.send(json.dumps({
        "type": "connect",
        "db_type": "postgresql",
        "host": "localhost",
        "user": "admin",
        "password": "secret",
        "database": "mydb"
    }))
    
    response = json.loads(await ws.recv())
    token = response["token"]
    connection_id = response["connection_id"]
    
    # 2. Share token with AI (via Claude Desktop config)
    # AI now has access to the database session
    
    # 3. AI calls tools → User receives approval requests
    # Example: AI calls db_query → User sees:
    # {
    #   "type": "approval_request",
    #   "request_id": "req_abc123",
    #   "tool": "db_query",
    #   "params": {"query": "SELECT * FROM users LIMIT 10"}
    # }
    
    # 4. User approves
    await ws.send(json.dumps({
        "type": "approve_command",
        "request_id": "req_abc123",
        "approved": True
    }))
    
    # 5. AI gets result
    # {... "rows": [...], "row_count": 10 ...}
    
    # 6. Disconnect
    await ws.send(json.dumps({"type": "disconnect"}))

asyncio.run(workflow())
```

## 🤝 Contributing

Contributions are welcome! The modular structure makes it easy to add new modules:

```bash
# Add a new module
mkdir -p src/modules/newmodule/{config,tools,skills}

# Create route
touch src/routes/newmodule.py

# Register in src/routes/__init__.py
from .newmodule import setup_newmodule
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
