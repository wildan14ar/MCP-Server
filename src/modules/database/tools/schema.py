"""
Schema Inspection Tools - Database schema discovery and exploration.

Provides tools for:
- Listing tables
- Getting table schema (columns, types, constraints)
- Inspecting indexes and foreign keys
- Getting table statistics
"""

from typing import Optional, List, Dict, Any
from ..config.connection import DatabaseConnection
from ..config.tools import tool


@tool(name="db_tables")
async def list_tables(connection_id: str) -> dict:
    """
    List all tables in the database.

    Args:
        connection_id: Connection ID from db_connect

    Returns:
        List of table names
    """
    schema_result = DatabaseConnection.get_schema(connection_id)

    if schema_result.get("status") == "error":
        return schema_result

    tables = list(schema_result.get("schema", {}).keys())

    return {
        "status": "success",
        "connection_id": connection_id,
        "total": len(tables),
        "tables": tables
    }


@tool(name="db_schema")
async def get_table_schema(
    connection_id: str,
    table_name: Optional[str] = None,
) -> dict:
    """
    Get detailed schema information for tables.

    If table_name is provided, returns schema for that table only.
    Otherwise, returns schema for all tables.

    Args:
        connection_id: Connection ID from db_connect
        table_name: Specific table name (optional)

    Returns:
        Detailed schema information including columns, types, constraints
    """
    schema_result = DatabaseConnection.get_schema(connection_id, table_name)

    return schema_result


@tool(name="db_columns")
async def get_table_columns(
    connection_id: str,
    table_name: str,
) -> dict:
    """
    Get column information for a specific table.

    Args:
        connection_id: Connection ID from db_connect
        table_name: Table name

    Returns:
        List of columns with names, types, constraints
    """
    schema_result = DatabaseConnection.get_schema(connection_id, table_name)

    if schema_result.get("status") == "error":
        return schema_result

    schema = schema_result.get("schema", {})
    if table_name not in schema:
        return {
            "status": "error",
            "message": f"Table '{table_name}' not found"
        }

    table_schema = schema[table_name]
    columns = table_schema.get("columns", [])

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "total_columns": len(columns),
        "columns": columns
    }


@tool(name="db_primary_key")
async def get_primary_key(
    connection_id: str,
    table_name: str,
) -> dict:
    """
    Get primary key information for a table.

    Args:
        connection_id: Connection ID from db_connect
        table_name: Table name

    Returns:
        Primary key column(s)
    """
    schema_result = DatabaseConnection.get_schema(connection_id, table_name)

    if schema_result.get("status") == "error":
        return schema_result

    schema = schema_result.get("schema", {})
    if table_name not in schema:
        return {
            "status": "error",
            "message": f"Table '{table_name}' not found"
        }

    table_schema = schema[table_name]
    primary_key = table_schema.get("primary_key", [])

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "primary_key": primary_key
    }


@tool(name="db_foreign_keys")
async def get_foreign_keys(
    connection_id: str,
    table_name: str,
) -> dict:
    """
    Get foreign key relationships for a table.

    Args:
        connection_id: Connection ID from db_connect
        table_name: Table name

    Returns:
        List of foreign keys with references
    """
    schema_result = DatabaseConnection.get_schema(connection_id, table_name)

    if schema_result.get("status") == "error":
        return schema_result

    schema = schema_result.get("schema", {})
    if table_name not in schema:
        return {
            "status": "error",
            "message": f"Table '{table_name}' not found"
        }

    table_schema = schema[table_name]
    foreign_keys = table_schema.get("foreign_keys", [])

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "total_foreign_keys": len(foreign_keys),
        "foreign_keys": foreign_keys
    }


@tool(name="db_indexes")
async def get_table_indexes(
    connection_id: str,
    table_name: str,
) -> dict:
    """
    Get indexes for a specific table.

    Args:
        connection_id: Connection ID from db_connect
        table_name: Table name

    Returns:
        List of indexes with columns and uniqueness
    """
    schema_result = DatabaseConnection.get_schema(connection_id, table_name)

    if schema_result.get("status") == "error":
        return schema_result

    schema = schema_result.get("schema", {})
    if table_name not in schema:
        return {
            "status": "error",
            "message": f"Table '{table_name}' not found"
        }

    table_schema = schema[table_name]
    indexes = table_schema.get("indexes", [])

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "total_indexes": len(indexes),
        "indexes": indexes
    }


@tool(name="db_relationships")
async def get_table_relationships(
    connection_id: str,
    table_name: str,
) -> dict:
    """
    Get all relationships for a table (both incoming and outgoing).

    Shows which tables this table references and which tables reference this table.

    Args:
        connection_id: Connection ID from db_connect
        table_name: Table name

    Returns:
        Relationship diagram data
    """
    schema_result = DatabaseConnection.get_schema(connection_id)

    if schema_result.get("status") == "error":
        return schema_result

    all_schema = schema_result.get("schema", {})

    # Outgoing: tables this table references
    outgoing = []
    if table_name in all_schema:
        for fk in all_schema[table_name].get("foreign_keys", []):
            outgoing.append({
                "from_table": table_name,
                "from_columns": fk.get("constrained_columns", []),
                "to_table": fk.get("referred_table", ""),
                "to_columns": fk.get("referred_columns", []),
            })

    # Incoming: tables that reference this table
    incoming = []
    for other_table, other_schema in all_schema.items():
        if other_table == table_name:
            continue
        for fk in other_schema.get("foreign_keys", []):
            if fk.get("referred_table") == table_name:
                incoming.append({
                    "from_table": other_table,
                    "from_columns": fk.get("constrained_columns", []),
                    "to_table": table_name,
                    "to_columns": fk.get("referred_columns", []),
                })

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "outgoing_relationships": outgoing,
        "incoming_relationships": incoming,
        "total_outgoing": len(outgoing),
        "total_incoming": len(incoming)
    }


@tool(name="db_table_stats")
async def get_table_stats(
    connection_id: str,
    table_name: str,
) -> dict:
    """
    Get statistics for a specific table (row count, column count, etc.).

    Args:
        connection_id: Connection ID from db_connect
        table_name: Table name

    Returns:
        Table statistics
    """
    # Get schema info
    schema_result = DatabaseConnection.get_schema(connection_id, table_name)

    if schema_result.get("status") == "error":
        return schema_result

    schema = schema_result.get("schema", {})
    if table_name not in schema:
        return {
            "status": "error",
            "message": f"Table '{table_name}' not found"
        }

    table_schema = schema[table_name]
    column_count = len(table_schema.get("columns", []))
    fk_count = len(table_schema.get("foreign_keys", []))
    index_count = len(table_schema.get("indexes", []))

    # Get row count
    conn = DatabaseConnection._connections.get(connection_id)
    row_count = 0
    if conn:
        try:
            row_count = conn.get_table_count(table_name)
        except Exception:
            row_count = -1  # Unknown

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "row_count": row_count,
        "column_count": column_count,
        "foreign_key_count": fk_count,
        "index_count": index_count,
        "primary_key": table_schema.get("primary_key", [])
    }


@tool(name="db_column_types")
async def get_column_types(
    connection_id: str,
    table_name: str,
) -> dict:
    """
    Get a simplified view of column types for a table.

    Args:
        connection_id: Connection ID from db_connect
        table_name: Table name

    Returns:
        Dictionary mapping column names to their types
    """
    columns_result = await get_table_columns(connection_id, table_name)

    if columns_result.get("status") != "success":
        return columns_result

    columns = columns_result.get("columns", [])
    type_map = {col["name"]: col["type"] for col in columns}

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "column_types": type_map
    }


@tool(name="db_search_tables")
async def search_tables(
    connection_id: str,
    search_term: str,
) -> dict:
    """
    Search for tables by name.

    Args:
        connection_id: Connection ID from db_connect
        search_term: Search string to match table names

    Returns:
        List of matching tables
    """
    tables_result = await list_tables(connection_id)

    if tables_result.get("status") != "success":
        return tables_result

    all_tables = tables_result.get("tables", [])
    matching = [t for t in all_tables if search_term.lower() in t.lower()]

    return {
        "status": "success",
        "connection_id": connection_id,
        "search_term": search_term,
        "total_found": len(matching),
        "tables": matching
    }
