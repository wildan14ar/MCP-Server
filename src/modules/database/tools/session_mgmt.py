"""
Database Session Management - Create new DB connections via MCP.

AI can create NEW database connections WITHOUT sending credentials.
Credentials come from the stored WS session credentials.

These tools DO NOT require user approval.
"""

from typing import Optional
from ..config.connection import DatabaseConnection
from src.lib.gatekeeper import get_credentials


async def create_database_connection(
    db_type: str,
    host: str,
    database: str,
    port: int = 5432,
) -> dict:
    """
    Create a new database connection using stored credentials.

    AI does NOT send credentials - they come from the user's WS session.

    Args:
        db_type: Database type (postgresql, mysql, sqlite, mssql, oracle)
        host: Database host
        database: Database name
        port: Database port (default: 5432)

    Returns:
        New connection ID
    """
    # Get stored credentials from WS session
    creds = get_credentials("database")
    if not creds:
        return {
            "status": "error",
            "message": "No stored credentials. User must connect via WebSocket first."
        }

    try:
        conn_id = DatabaseConnection.create(
            db_type=db_type,
            host=host,
            user=creds["user"],
            password=creds.get("password"),
            database=database,
            port=port,
        )
        return {
            "status": "success",
            "connection_id": conn_id,
            "db_type": db_type,
            "host": host,
            "database": database,
            "user": creds["user"],
            "message": f"New {db_type} connection created to {host}/{database}. Use connection_id for queries."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def list_database_connections() -> dict:
    """
    List all active database connections.

    Returns:
        List of active connections
    """
    connections = DatabaseConnection.list()
    return {
        "status": "success",
        "connections": connections,
        "total": len(connections)
    }


async def close_database_connection(connection_id: str) -> dict:
    """
    Close a database connection.

    Args:
        connection_id: Connection ID from db_connect or db_new_connection

    Returns:
        Status message
    """
    success = DatabaseConnection.close(connection_id)
    if success:
        return {
            "status": "success",
            "connection_id": connection_id,
            "message": "Connection closed"
        }
    return {
        "status": "error",
        "message": f"Connection '{connection_id}' not found"
    }


def register_session_tools(mcp):
    """Register session management tools manually (not via @tool decorator) so params are visible."""
    mcp.tool(name="db_new_connection")(create_database_connection)
    mcp.tool(name="db_list_connections")(list_database_connections)
    mcp.tool(name="db_close_connection")(close_database_connection)
