<p align="center">
  <img src="https://raw.githubusercontent.com/haris-musa/excel-mcp-server/main/assets/logo.png" alt="Excel MCP Server Logo" width="300"/>
</p>

[![PyPI version](https://img.shields.io/pypi/v/excel-mcp-server.svg)](https://pypi.org/project/excel-mcp-server/)
[![Total Downloads](https://static.pepy.tech/badge/excel-mcp-server)](https://pepy.tech/project/excel-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![smithery badge](https://smithery.ai/badge/@haris-musa/excel-mcp-server)](https://smithery.ai/server/@haris-musa/excel-mcp-server)

# MCP Server - Modular Architecture

A **Model Context Protocol (MCP)** server with modular architecture supporting:
- 📊 **Excel Operations** - Manipulate Excel files without Microsoft Excel
- 🖥️ **SSH Server Management** - Remote server operations via WebSocket + MCP tools

## 🏗️ Architecture Overview

```
src/
├── modules/
│   ├── excel/              # 📊 Excel Module
│   │   ├── operations/     # Core Excel operations (12 files)
│   │   ├── tools/          # MCP tool registration
│   │   └── routes/         # FastAPI endpoints
│   └── server/             # 🖥️ Server Module
│       ├── config/         # SSH session & WebSocket
│       ├── tools/          # MCP tools (25+ operations)
│       └── routes/         # FastAPI endpoints
└── server.py               # Main entry point
```

### Modular Design Benefits

- ✅ **Independent Modules** - Excel and Server operate independently
- ✅ **Scalable** - Easy to add new modules (database, storage, etc.)
- ✅ **Maintainable** - Changes isolated to specific modules
- ✅ **Reusable** - Modules can import from each other
- ✅ **Clean Separation** - Clear responsibility boundaries

## 📊 Module 1: Excel

### Features

- 📈 **Data Manipulation**: Formulas, formatting, charts, pivot tables
- 🔍 **Data Validation**: Built-in validation for ranges and formulas
- 🎨 **Formatting**: Font styling, colors, borders, alignment
- 📋 **Table Operations**: Create and manage Excel tables
- 📊 **Chart Creation**: Line, bar, pie, scatter charts
- 🔄 **Pivot Tables**: Dynamic pivot tables for analysis
- 🔧 **Sheet Management**: Copy, rename, delete worksheets

### Quick Start

```python
from src.modules.excel.tools import excel_tools
from src.modules.excel.operations import workbook, sheet, data

# Register MCP tools
excel_tools(mcp, get_excel_path)

# Direct operations
workbook.create_workbook("report.xlsx")
sheet.create_sheet("report.xlsx", "Sales")
data.write_data("report.xlsx", "Sales", [[1, 2, 3]], "A1")
```

### Available Operations (12)

| Operation | Description |
|-----------|-------------|
| `workbook` | Create, open, save workbooks |
| `sheet` | Sheet management (create, delete, copy) |
| `data` | Read/write data |
| `formatting` | Cell and range formatting |
| `calculations` | Formulas and calculations |
| `chart` | Chart creation |
| `tables` | Excel table operations |
| `pivot` | Pivot table creation |
| `validation` | Data validation |
| `cell_utils` | Cell utility functions |
| `cell_validation` | Cell validation helpers |
| `exceptions` | Custom exceptions |

📖 **[Complete Excel Documentation →](docs/EXCEL.md)**

## 🖥️ Module 2: Server

### Features

- 🔐 **Token Authentication** - Secure token-based access
- 🌐 **WebSocket Support** - Real-time bidirectional communication
- 🛠️ **25+ MCP Tools** - Comprehensive server operations
- ✅ **Command Confirmation** - Safety for dangerous operations
- 📊 **Session Management** - Multi-session support
- 🔄 **State Consistency** - Shared state between WebSocket and MCP

### Architecture Flow

```
┌─────────────────────────────────────────────────┐
│  1. WebSocket Connect                           │
│     ↓                                           │
│  2. SSH Session Created + Token Generated       │
│     ↓                                           │
│  ┌──────────────────────────────────────┐      │
│  │  DUAL ACCESS (Same Session):         │      │
│  │                                       │      │
│  │  A) WebSocket (Real-time)             │      │
│  │     - Interactive commands            │      │
│  │     - Live output streaming           │      │
│  │                                       │      │
│  │  B) MCP Tools (Token-based)           │      │
│  │     - REST API with token             │      │
│  │     - Execute in same session         │      │
│  └──────────────────────────────────────┘      │
│     ↓                                           │
│  3. WebSocket Disconnect = Token Invalid        │
└─────────────────────────────────────────────────┘
```

### Quick Start

```python
from src.modules.server.tools import register_server_tools
from src.modules.server.routes import router
from src.modules.server.config import SSHSession

# Register MCP tools
register_server_tools(mcp)

# Add routes
app.include_router(router)

# WebSocket: ws://localhost:8017/server/ws
# REST API: POST /server/mcp/execute
```

### Available Operations (25+)

| Category | Tools |
|----------|-------|
| **Basic Info** | whoami, pwd, hostname, uname |
| **File Listing** | ls, tree |
| **File Search** | find_files, grep_files, locate_file |
| **File Operations** | cat_file, tail_file, head_file, file_info |
| **System Info** | disk_usage, memory_usage, process_list, uptime_info |
| **Network** | network_interfaces, ping_host |
| **Core** | execute_ssh_command, test_ssh_connection |

📖 **[Complete Server Documentation →](docs/SERVER.md)**

## 🚀 Installation & Usage

### Prerequisites

```bash
pip install fastmcp paramiko websockets openpyxl
```

### Running the Server

```bash
# Start server with both modules
cd MCP-Server
python -m src.server run_sse

# Server runs on http://localhost:8017
```

### Using with Claude Desktop

```json
{
  "mcpServers": {
    "mcp-server": {
      "command": "python",
      "args": ["-m", "src.server", "run_sse"],
      "cwd": "/path/to/MCP-Server",
      "env": {
        "FASTMCP_PORT": "8017",
        "EXCEL_FILES_PATH": "/path/to/excel_files"
      }
    }
  }
}
```

## 📦 Module Integration Example

### Scenario: Generate Server Report in Excel

```python
import asyncio
import websockets
import requests
import json
from src.modules.excel.operations import workbook, sheet, data

async def generate_server_report():
    # 1. Connect to server via WebSocket
    ws = await websockets.connect("ws://localhost:8017/server/ws")
    
    await ws.send(json.dumps({
        "type": "connect",
        "host": "server.com",
        "user": "admin",
        "password": "secret"
    }))
    
    response = json.loads(await ws.recv())
    token = response["token"]
    
    # 2. Get server info using MCP tools
    headers = {"X-MCP-Token": token}
    
    disk = requests.post(
        "http://localhost:8017/server/mcp/execute",
        headers=headers,
        json={"command": "df -h"}
    ).json()
    
    memory = requests.post(
        "http://localhost:8017/server/mcp/execute",
        headers=headers,
        json={"command": "free -h"}
    ).json()
    
    # 3. Generate Excel report
    workbook.create_workbook("server_report.xlsx")
    sheet.create_sheet("server_report.xlsx", "System Info")
    
    data.write_data(
        "server_report.xlsx",
        "System Info",
        [
            ["Metric", "Value"],
            ["Disk Usage", disk["stdout"]],
            ["Memory Usage", memory["stdout"]]
        ],
        "A1"
    )
    
    # 4. Disconnect
    await ws.send(json.dumps({"type": "disconnect"}))
    await ws.close()
    
    print("✅ Report generated: server_report.xlsx")

asyncio.run(generate_server_report())
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTMCP_HOST` | Server host | `0.0.0.0` |
| `FASTMCP_PORT` | Server port | `8017` |
| `EXCEL_FILES_PATH` | Excel files directory | `./excel_files` |

### Transport Methods

1. **Stdio** (Local use)
   ```bash
   python -m src.server stdio
   ```

2. **SSE** (Server-Sent Events)
   ```bash
   python -m src.server run_sse
   ```

3. **Streamable HTTP** (Recommended for remote)
   ```bash
   python -m src.server streamable_http
   ```

## 📚 Documentation

- **[Excel Module Documentation](docs/EXCEL.md)** - Complete Excel MCP tools reference
- **[Server Module Documentation](docs/SERVER.md)** - Complete Server MCP tools reference
- **[Modular Structure](docs/MODULAR_STRUCTURE.md)** - Architecture details

## 🤝 Contributing

Contributions are welcome! The modular structure makes it easy to add new modules:

```bash
# Add a new module
mkdir -p src/modules/database/{config,tools,routes,operations}
touch src/modules/database/__init__.py

# Update modules/__init__.py
__all__ = ["server", "excel", "database"]
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=haris-musa/excel-mcp-server&type=Date)](https://www.star-history.com/#haris-musa/excel-mcp-server&Date)
