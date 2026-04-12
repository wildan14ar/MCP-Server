"""
Core Database Tools - Query execution and connection management.

Provides tools for:
- Database connection management
- Query execution (SELECT, INSERT, UPDATE, DELETE)
- Transaction management

NOTE: All execution tools require user approval before execution.
Read-only tools (schema, tables, columns) do not require approval.
"""

# NOTE: Session management (connect/disconnect) is handled via WebSocket only.
# AI cannot create new sessions - it can only use existing sessions via connection_id.
# This ensures credentials are always provided by user, not AI.

from typing import Optional, List, Dict, Any
from ..config.connection import DatabaseConnection
from ..config.tools import tool
from ...lib.gatekeeper import gatekeeper


@tool(name="db_query")
async def database_query(
    connection_id: str,
    query: str,
    params: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Execute a SQL query on a database connection.

    Requires user approval before execution.

    Args:
        connection_id: Connection ID from db_connect
        query: SQL query to execute
        params: Query parameters (for parameterized queries)

    Returns:
        Query results with columns, rows, and metadata
    """
    # Create approval request (broadcast to all connected users)
    request = gatekeeper.create_request("db_query", {"query": query, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    # Execute query
    result = DatabaseConnection.execute(connection_id, query, params)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "query": query,
        "columns": result.get("columns", []),
        "rows": result.get("rows", []),
        "row_count": result.get("row_count", 0),
        "execution_time": result.get("execution_time", 0),
    }


@tool(name="db_query_single")
async def query_single_row(
    connection_id: str,
    query: str,
    params: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Execute a SQL query and return only the first row.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("db_query_single", {"query": query, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = DatabaseConnection.execute(connection_id, query, params)

    if result.get("status") == "error":
        return result

    rows = result.get("rows", [])
    row = rows[0] if rows else None

    return {
        "status": "success",
        "connection_id": connection_id,
        "row": row,
        "found": row is not None,
    }


@tool(name="db_query_count")
async def query_row_count(
    connection_id: str,
    query: str,
    params: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Execute a query and return only the row count.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("db_query_count", {"query": query, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = DatabaseConnection.execute(connection_id, query, params)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "row_count": result.get("row_count", 0),
    }


@tool(name="db_transaction_start")
async def transaction_start(
    connection_id: str,
) -> dict:
    """
    Begin a new database transaction.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("db_transaction_start", {"connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    conn = DatabaseConnection._connections.get(connection_id)
    if not conn:
        return {
            "status": "error",
            "message": f"Connection {connection_id} not found"
        }

    try:
        conn.begin_transaction()
        return {
            "status": "success",
            "connection_id": connection_id,
            "message": "Transaction started"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@tool(name="db_transaction_commit")
async def transaction_commit(
    connection_id: str,
) -> dict:
    """
    Commit the current transaction.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("db_transaction_commit", {"connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    conn = DatabaseConnection._connections.get(connection_id)
    if not conn:
        return {
            "status": "error",
            "message": f"Connection {connection_id} not found"
        }

    try:
        conn.commit_transaction()
        return {
            "status": "success",
            "connection_id": connection_id,
            "message": "Transaction committed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@tool(name="db_transaction_rollback")
async def transaction_rollback(
    connection_id: str,
) -> dict:
    """
    Rollback the current transaction.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("db_transaction_rollback", {"connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    conn = DatabaseConnection._connections.get(connection_id)
    if not conn:
        return {
            "status": "error",
            "message": f"Connection {connection_id} not found"
        }

    try:
        conn.rollback_transaction()
        return {
            "status": "success",
            "connection_id": connection_id,
            "message": "Transaction rolled back"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@tool(name="db_insert")
async def database_insert(
    connection_id: str,
    table: str,
    data: Dict[str, Any],
) -> dict:
    """
    Insert a single row into a table.

    Requires user approval before execution.
    """
    columns = ", ".join(data.keys())
    placeholders = ", ".join([f":{k}" for k in data.keys()])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    request = gatekeeper.create_request("db_insert", {"table": table, "data": data, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = DatabaseConnection.execute(connection_id, query, data)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table,
        "message": f"Inserted 1 row into {table}"
    }


@tool(name="db_update")
async def database_update(
    connection_id: str,
    table: str,
    data: Dict[str, Any],
    where_column: str,
    where_value: Any,
) -> dict:
    """
    Update rows in a table.

    Requires user approval before execution.
    """
    set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
    data["_where_value"] = where_value
    query = f"UPDATE {table} SET {set_clause} WHERE {where_column} = :_where_value"

    request = gatekeeper.create_request("db_update", {"table": table, "data": data, "where": f"{where_column}={where_value}", "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = DatabaseConnection.execute(connection_id, query, data)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table,
        "message": f"Updated rows in {table} where {where_column} = {where_value}"
    }


@tool(name="db_delete")
async def database_delete(
    connection_id: str,
    table: str,
    where_column: str,
    where_value: Any,
) -> dict:
    """
    Delete rows from a table.

    Requires user approval before execution.
    """
    query = f"DELETE FROM {table} WHERE {where_column} = :where_value"

    request = gatekeeper.create_request("db_delete", {"table": table, "where": f"{where_column}={where_value}", "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = DatabaseConnection.execute(connection_id, query, {"where_value": where_value})

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table,
        "message": f"Deleted rows from {table} where {where_column} = {where_value}"
    }


@tool(name="db_clear_cache")
async def clear_query_cache(connection_id: str) -> dict:
    """
    Clear the query cache for a connection.

    NOTE: Read-only operation, no approval required.
    """
    conn = DatabaseConnection._connections.get(connection_id)
    if not conn:
        return {
            "status": "error",
            "message": f"Connection {connection_id} not found"
        }

    conn.clear_cache()
    return {
        "status": "success",
        "connection_id": connection_id,
        "message": "Query cache cleared"
    }
