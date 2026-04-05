# 🗄️ Database MCP Module - Complete Documentation

## 🖥️ Overview

The Database module provides database management through **WebSocket** and **MCP tools** with connection pooling and session state. Built for real-time database operations with token-based security.

## 🏗️ Module Structure

```
modules/database/
├── config/                     # Configuration & Connection Management
│   ├── connection.py          # Database connection with session management
│   └── tools.py               # MCP tool registry & decorator
├── tools/                      # MCP Tools Implementation
│   ├── core.py                # Connection & query tools (11 tools)
│   ├── schema.py              # Schema inspection tools (9 tools)
│   └── admin.py               # Database admin tools (13 tools)
└── main.py                     # FastAPI router & WebSocket handler
```

## 🎯 Key Features

- 🔐 **Token Authentication** - Secure token per WebSocket session
- 🌐 **WebSocket Support** - Real-time bidirectional communication
- 🛠️ **33+ MCP Tools** - Comprehensive database operations
- 💾 **Multi-Database** - PostgreSQL, MySQL, SQLite, MSSQL, Oracle
- 📊 **Connection Pooling** - Multiple concurrent connections
- 🔄 **Transaction Support** - Begin, commit, rollback
- 🔍 **Schema Discovery** - Tables, columns, indexes, relationships
- ⚡ **Query Caching** - Automatic SELECT query caching (5 min TTL)

## 🚀 Architecture Flow

```
┌──────────────────────────────────────────────────────────────┐
│                     SESSION LIFECYCLE                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Client → WebSocket Connect                               │
│     ws://localhost:8017/database/ws                          │
│                                                              │
│  2. Client → Database Connection Request                     │
│     {"type": "connect", "db_type": "postgresql", ...}        │
│                                                              │
│  3. Server → Database Session Created                        │
│     - Establish database connection                           │
│     - Generate unique token (32-byte URL-safe)               │
│     - Map token to session                                   │
│                                                              │
│  4. Server → Send Token to Client                            │
│     {"type": "connected", "token": "...", ...}               │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  SESSION ACTIVE - DUAL ACCESS:                         │ │
│  │                                                        │ │
│  │  A) WebSocket (Real-time Interactive)                 │ │
│  │     - Execute queries with results streaming          │ │
│  │     - Schema exploration                              │ │
│  │     - Transaction management                          │ │
│  │     - Command: ws.send({"type": "query", ...})        │ │
│  │                                                        │ │
│  │  B) MCP Tools (Token-based REST API)                  │ │
│  │     - Execute tools in same connection                │ │
│  │     - Token in header: X-MCP-Token                    │ │
│  │     - Endpoint: POST /database/mcp                    │ │
│  │                                                        │ │
│  │  ⚡ SHARED STATE:                                      │ │
│  │     - Same database connection                        │ │
│  │     - Same transaction context                        │ │
│  │     - Same query cache                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  5. Client → Disconnect                                      │
│     {"type": "disconnect"}                                   │
│                                                              │
│  6. Server → Cleanup                                         │
│     - Close database connection                              │
│     - Invalidate token                                       │
│     - Remove session from mapping                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 📚 Available MCP Tools (33+)

### Connection Management (4)

| Tool | Description | Example |
|------|-------------|---------|
| `db_connect` | Create database connection | Connect to PostgreSQL |
| `db_disconnect` | Close connection | Disconnect by ID |
| `db_list_connections` | List active connections | Show all connections |
| `db_test_connection` | Test if connection is alive | Check connectivity |

### Query Execution (6)

| Tool | Description | Example |
|------|-------------|---------|
| `db_query` | Execute SQL query | SELECT, INSERT, UPDATE, DELETE |
| `db_query_single` | Get first row only | SELECT * WHERE id=1 |
| `db_query_count` | Get row count only | COUNT results |
| `db_insert` | Insert single row | INSERT INTO users ... |
| `db_update` | Update rows | UPDATE users SET ... |
| `db_delete` | Delete rows | DELETE FROM users WHERE ... |

### Transaction Management (3)

| Tool | Description | Example |
|------|-------------|---------|
| `db_transaction_start` | Begin transaction | START TRANSACTION |
| `db_transaction_commit` | Commit transaction | COMMIT |
| `db_transaction_rollback` | Rollback transaction | ROLLBACK |

### Schema Discovery (9)

| Tool | Description | Example |
|------|-------------|---------|
| `db_tables` | List all tables | Show tables |
| `db_schema` | Get table schema(s) | DESCRIBE tables |
| `db_columns` | Get column info | Columns of users table |
| `db_primary_key` | Get primary key | PK of orders |
| `db_foreign_keys` | Get foreign keys | FK relationships |
| `db_indexes` | Get indexes | Indexes on table |
| `db_relationships` | Table relationships | ER diagram data |
| `db_table_stats` | Table statistics | Row count, column count |
| `db_column_types` | Column type mapping | Name → Type map |

### Database Admin (11)

| Tool | Description | Example |
|------|-------------|---------|
| `db_create_table` | Create new table | CREATE TABLE users ... |
| `db_drop_table` | Drop table | DROP TABLE users |
| `db_add_column` | Add column | ALTER TABLE ADD COLUMN |
| `db_drop_column` | Drop column | ALTER TABLE DROP COLUMN |
| `db_alter_column` | Modify column | Change type, name, constraints |
| `db_create_index` | Create index | CREATE INDEX idx_name |
| `db_drop_index` | Drop index | DROP INDEX idx_name |
| `db_create_view` | Create view | CREATE VIEW v_users |
| `db_drop_view` | Drop view | DROP VIEW v_users |
| `db_truncate_table` | Truncate table | Remove all rows |
| `db_rename_table` | Rename table | ALTER TABLE RENAME |

### Utilities (1)

| Tool | Description | Example |
|------|-------------|---------|
| `db_clear_cache` | Clear query cache | Clear cached results |
| `db_search_tables` | Search tables by name | Find tables with "user" |

## 💡 Usage Examples

### Example 1: Connect & Query via WebSocket

```python
import asyncio
import websockets
import json

async def query_database():
    uri = "ws://localhost:8017/database/ws"
    
    async with websockets.connect(uri) as ws:
        # 1. Connect to database
        await ws.send(json.dumps({
            "type": "connect",
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "user": "admin",
            "password": "secret",
            "database": "mydb"
        }))
        
        response = json.loads(await ws.recv())
        print(f"✅ Connected: {response['connection_id']}")
        print(f"🔑 Token: {response['token']}")
        
        # 2. Execute query
        await ws.send(json.dumps({
            "type": "query",
            "query": "SELECT * FROM users LIMIT 10"
        }))
        
        result = json.loads(await ws.recv())
        print(f"📊 Found {result['row_count']} rows")
        for row in result['rows']:
            print(f"  - {row}")
        
        # 3. Get schema
        await ws.send(json.dumps({
            "type": "schema",
            "table_name": "users"
        }))
        
        schema = json.loads(await ws.recv())
        print(f"📋 Schema: {schema['schema']}")
        
        # 4. Disconnect
        await ws.send(json.dumps({"type": "disconnect"}))

asyncio.run(query_database())
```

### Example 2: Use MCP Tools via REST API

```python
import requests

# Token from WebSocket connection
TOKEN = "your_token_from_websocket"
headers = {"X-MCP-Token": TOKEN}

# 1. List tables
response = requests.post(
    "http://localhost:8017/database/mcp",
    headers=headers,
    json={"tool": "db_tables", "connection_id": "conn_id"}
)
print(f"Tables: {response.json()}")

# 2. Execute query
response = requests.post(
    "http://localhost:8017/database/mcp",
    headers=headers,
    json={
        "tool": "db_query",
        "connection_id": "conn_id",
        "query": "SELECT COUNT(*) FROM orders"
    }
)
print(f"Order count: {response.json()}")

# 3. Get schema
response = requests.post(
    "http://localhost:8017/database/mcp",
    headers=headers,
    json={
        "tool": "db_schema",
        "connection_id": "conn_id",
        "table_name": "products"
    }
)
print(f"Schema: {response.json()}")
```

### Example 3: Transaction Management

```python
async def transaction_example():
    uri = "ws://localhost:8017/database/ws"
    
    async with websockets.connect(uri) as ws:
        # Connect
        await ws.send(json.dumps({
            "type": "connect",
            "db_type": "postgresql",
            "host": "localhost",
            "user": "admin",
            "password": "secret",
            "database": "mydb"
        }))
        
        await ws.recv()  # Connected response
        
        # Start transaction
        await ws.send(json.dumps({"type": "transaction_start"}))
        await ws.recv()  # Transaction started
        
        # Execute multiple queries
        await ws.send(json.dumps({
            "type": "query",
            "query": "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
        }))
        await ws.recv()  # Result
        
        await ws.send(json.dumps({
            "type": "query",
            "query": "INSERT INTO orders (user_id, total) VALUES (1, 99.99)"
        }))
        await ws.recv()  # Result
        
        # Commit
        await ws.send(json.dumps({"type": "transaction_commit"}))
        result = json.loads(await ws.recv())
        print(f"✅ Transaction committed: {result}")
```

### Example 4: Schema Discovery Workflow

```python
async def discover_schema():
    uri = "ws://localhost:8017/database/ws"
    
    async with websockets.connect(uri) as ws:
        # Connect
        await ws.send(json.dumps({
            "type": "connect",
            "db_type": "postgresql",
            "host": "localhost",
            "user": "admin",
            "password": "secret",
            "database": "ecommerce"
        }))
        
        await ws.recv()  # Connected
        
        # List all tables
        await ws.send(json.dumps({"type": "tables"}))
        result = json.loads(await ws.recv())
        tables = result['tables']
        print(f"📋 Tables: {tables}")
        
        # Get schema for each table
        for table in tables[:3]:  # First 3 tables
            await ws.send(json.dumps({
                "type": "schema",
                "table_name": table
            }))
            schema_result = json.loads(await ws.recv())
            print(f"\n📊 Table: {table}")
            for col in schema_result['schema'][table]['columns']:
                print(f"  - {col['name']}: {col['type']}")
```

## 🔧 Supported Database Types

### PostgreSQL
```json
{
  "db_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "user": "admin",
  "password": "secret",
  "database": "mydb",
  "schema": "public"  // optional
}
```

### MySQL
```json
{
  "db_type": "mysql",
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "password": "secret",
  "database": "mydb"
}
```

### SQLite
```json
{
  "db_type": "sqlite",
  "database": "/path/to/database.db"  // or ":memory:" for in-memory
}
```

### Microsoft SQL Server
```json
{
  "db_type": "mssql",
  "host": "localhost",
  "port": 1433,
  "user": "sa",
  "password": "secret",
  "database": "mydb"
}
```

### Oracle
```json
{
  "db_type": "oracle",
  "host": "localhost",
  "port": 1521,
  "user": "system",
  "password": "secret",
  "database": "ORCL"
}
```

## ⚙️ WebSocket Messages

### Connect to Database
```json
{
  "type": "connect",
  "db_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "user": "admin",
  "password": "secret",
  "database": "mydb",
  "schema": "public"
}
```

### Execute Query
```json
{
  "type": "query",
  "query": "SELECT * FROM users WHERE active = true",
  "params": {"active": true}
}
```

### Get Schema
```json
{
  "type": "schema",
  "table_name": "users"  // optional, omit for all tables
}
```

### List Tables
```json
{
  "type": "tables"
}
```

### Transaction Management
```json
{"type": "transaction_start"}
{"type": "query", "query": "INSERT INTO ..."}
{"type": "transaction_commit"}
// or
{"type": "transaction_rollback"}
```

### Disconnect
```json
{
  "type": "disconnect"
}
```

## 🔐 Best Practices

### 1. Connection Management
```python
# Always close connections when done
await ws.send(json.dumps({"type": "disconnect"}))

# Or use MCP tool
requests.post(url, headers=headers, json={
    "tool": "db_disconnect",
    "connection_id": "conn_id"
})
```

### 2. Query Security
```python
# Use parameterized queries to prevent SQL injection
await ws.send(json.dumps({
    "type": "query",
    "query": "SELECT * FROM users WHERE email = :email",
    "params": {"email": "user@example.com"}
}))
```

### 3. Transaction Safety
```python
# Always commit or rollback transactions
try:
    await ws.send(json.dumps({"type": "transaction_start"}))
    # ... execute queries ...
    await ws.send(json.dumps({"type": "transaction_commit"}))
except Exception:
    await ws.send(json.dumps({"type": "transaction_rollback"}))
```

### 4. Query Caching
```python
# SELECT queries are cached for 5 minutes
# Clear cache when data changes
await ws.send(json.dumps({"type": "query", "query": "DELETE FROM cache_table"}))
```

## 🆘 Troubleshooting

### Issue 1: Connection Failed

**Symptoms:** Cannot connect to database

**Solutions:**
```python
# Check database is running
# PostgreSQL: pg_isready -h localhost -p 5432
# MySQL: mysqladmin ping -h localhost

# Verify credentials
# Test with psql or mysql client first
```

### Issue 2: Query Timeout

**Symptoms:** Long-running query never returns

**Solutions:**
```python
# Add timeout to query
await ws.send(json.dumps({
    "type": "query",
    "query": "SET statement_timeout = '30s'; SELECT * FROM large_table"
}))

# Use LIMIT for large queries
await ws.send(json.dumps({
    "type": "query",
    "query": "SELECT * FROM users LIMIT 1000"
}))
```

### Issue 3: Transaction Error

**Symptoms:** Transaction commit fails

**Solutions:**
```python
# Always rollback on error
try:
    # ... transaction queries ...
    await ws.send(json.dumps({"type": "transaction_commit"}))
except Exception:
    await ws.send(json.dumps({"type": "transaction_rollback"}))
    raise
```

## 📝 Changelog

### v1.0.0 - Initial Release
- 🎉 WebSocket + MCP tools integration
- 🔐 Token-based session management
- 🛠️ 33+ database operation tools
- 💾 Multi-database support (PostgreSQL, MySQL, SQLite, MSSQL, Oracle)
- 🔄 Transaction support (begin, commit, rollback)
- 🔍 Schema discovery tools
- ⚡ Query caching with 5-minute TTL

---

**Last Updated:** 2026-04-04
**Module Version:** 1.0.0
**License:** MIT
