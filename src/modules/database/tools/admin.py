"""
Database Admin Tools - Schema modification and administrative operations.

Provides tools for:
- Creating tables
- Altering tables (add/drop/modify columns)
- Dropping tables
- Creating/dropping indexes
- Database backup/restore helpers

NOTE: All admin tools require user approval before execution.
"""

from typing import Optional, List, Dict, Any
from ..config.connection import DatabaseConnection
from ..config.tools import tool
from ...lib.gatekeeper import gatekeeper


@tool(name="db_create_table")
async def create_table(
    connection_id: str,
    table_name: str,
    columns: List[Dict[str, Any]],
) -> dict:
    """
    Create a new table with specified columns.

    Requires user approval before execution.
    """
    # Create approval request (broadcast to all connected users)
    request = gatekeeper.create_request("db_create_table", {"table_name": table_name, "columns": len(columns), "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    column_defs = []
    for col in columns:
        col_def = f"{col['name']} {col['type']}"

        if col.get("primary_key"):
            col_def += " PRIMARY KEY"

        if not col.get("nullable", True) and not col.get("primary_key"):
            col_def += " NOT NULL"

        if col.get("default"):
            col_def += f" DEFAULT {col['default']}"

        column_defs.append(col_def)

    columns_sql = ", ".join(column_defs)
    query = f"CREATE TABLE {table_name} ({columns_sql})"

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "message": f"Table '{table_name}' created with {len(columns)} columns"
    }


@tool(name="db_drop_table")
async def drop_table(
    connection_id: str,
    table_name: str,
    if_exists: bool = True,
) -> dict:
    """
    Drop (delete) a table.

    ⚠️ WARNING: This will permanently delete the table and all its data!
    Requires user approval before execution.
    """
    exists_clause = "IF EXISTS " if if_exists else ""
    query = f"DROP TABLE {exists_clause}{table_name}"

    # Create approval request
    request = gatekeeper.create_request("db_drop_table", {"table_name": table_name, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "message": f"Table '{table_name}' dropped"
    }


@tool(name="db_add_column")
async def add_column(
    connection_id: str,
    table_name: str,
    column_name: str,
    column_type: str,
    nullable: bool = True,
    default: Optional[str] = None,
) -> dict:
    """
    Add a new column to an existing table.
    Requires user approval before execution.
    """
    # Create approval request
    request = gatekeeper.create_request("db_add_column", {"table_name": table_name, "column_name": column_name, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    nullable_clause = "" if nullable else " NOT NULL"
    default_clause = f" DEFAULT {default}" if default else ""

    query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{nullable_clause}{default_clause}"

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "column": column_name,
        "message": f"Column '{column_name}' added to '{table_name}'"
    }


@tool(name="db_drop_column")
async def drop_column(
    connection_id: str,
    table_name: str,
    column_name: str,
) -> dict:
    """
    Drop (delete) a column from a table.
    ⚠️ WARNING: This will permanently delete the column and all its data!
    Requires user approval before execution.
    """
    # Create approval request
    request = gatekeeper.create_request("db_drop_column", {"table_name": table_name, "column_name": column_name, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    query = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "column": column_name,
        "message": f"Column '{column_name}' dropped from '{table_name}'"
    }


@tool(name="db_alter_column")
async def alter_column(
    connection_id: str,
    table_name: str,
    column_name: str,
    new_type: Optional[str] = None,
    new_name: Optional[str] = None,
    set_not_null: bool = False,
    drop_not_null: bool = False,
    set_default: Optional[str] = None,
    drop_default: bool = False,
) -> dict:
    """
    Alter an existing column's properties.
    Requires user approval before execution.
    """
    # Create approval request
    request = gatekeeper.create_request("db_alter_column", {"table_name": table_name, "column_name": column_name, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    conn = DatabaseConnection._connections.get(connection_id)
    if not conn:
        return {"status": "error", "message": "Connection not found"}

    db_type = conn.db_type

    if db_type == "postgresql":
        if new_name:
            query = f"ALTER TABLE {table_name} RENAME COLUMN {column_name} TO {new_name}"
        elif new_type:
            query = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {new_type}"
            if set_not_null:
                query = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET NOT NULL"
            elif drop_not_null:
                query = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP NOT NULL"
            if set_default:
                query = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET DEFAULT {set_default}"
            elif drop_default:
                query = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP DEFAULT"
        else:
            return {"status": "error", "message": "No alteration specified"}
    else:
        return {
            "status": "error",
            "message": f"ALTER COLUMN not supported for {db_type}. Use raw SQL instead."
        }

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "column": column_name,
        "message": f"Column '{column_name}' altered in '{table_name}'"
    }


@tool(name="db_create_index")
async def create_index(
    connection_id: str,
    table_name: str,
    index_name: str,
    columns: List[str],
    unique: bool = False,
) -> dict:
    """
    Create an index on a table.
    Requires user approval before execution.
    """
    # Create approval request
    request = gatekeeper.create_request("db_create_index", {"table_name": table_name, "index_name": index_name, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    unique_clause = "UNIQUE " if unique else ""
    columns_str = ", ".join(columns)
    query = f"CREATE {unique_clause}INDEX {index_name} ON {table_name} ({columns_str})"

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "index": index_name,
        "columns": columns,
        "unique": unique,
        "message": f"Index '{index_name}' created on {table_name}({columns_str})"
    }


@tool(name="db_drop_index")
async def drop_index(
    connection_id: str,
    index_name: str,
    table_name: Optional[str] = None,
) -> dict:
    """
    Drop an index.
    Requires user approval before execution.
    """
    # Create approval request
    request = gatekeeper.create_request("db_drop_index", {"index_name": index_name, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    conn = DatabaseConnection._connections.get(connection_id)
    if not conn:
        return {"status": "error", "message": "Connection not found"}

    db_type = conn.db_type

    if db_type == "postgresql":
        query = f"DROP INDEX {index_name}"
    elif db_type == "mysql":
        query = f"ALTER TABLE {table_name} DROP INDEX {index_name}"
    else:
        query = f"DROP INDEX {index_name} ON {table_name}"

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "index": index_name,
        "message": f"Index '{index_name}' dropped"
    }


@tool(name="db_create_view")
async def create_view(
    connection_id: str,
    view_name: str,
    query: str,
    or_replace: bool = True,
) -> dict:
    """
    Create a database view.
    Requires user approval before execution.
    """
    # Create approval request
    request = gatekeeper.create_request("db_create_view", {"view_name": view_name, "query": query, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    replace_clause = "OR REPLACE " if or_replace else ""
    query_full = f"CREATE {replace_clause}VIEW {view_name} AS {query}"

    result = DatabaseConnection.execute(connection_id, query_full)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "view": view_name,
        "message": f"View '{view_name}' created"
    }


@tool(name="db_drop_view")
async def drop_view(
    connection_id: str,
    view_name: str,
) -> dict:
    """
    Drop a view.
    Requires user approval before execution.
    """
    # Create approval request
    request = gatekeeper.create_request("db_drop_view", {"view_name": view_name, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    query = f"DROP VIEW IF EXISTS {view_name}"

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "view": view_name,
        "message": f"View '{view_name}' dropped"
    }


@tool(name="db_truncate_table")
async def truncate_table(
    connection_id: str,
    table_name: str,
) -> dict:
    """
    Truncate a table (remove all rows quickly).
    ⚠️ WARNING: This will permanently delete all data in the table!
    Requires user approval before execution.
    """
    # Create approval request
    request = gatekeeper.create_request("db_truncate_table", {"table_name": table_name, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    query = f"TRUNCATE TABLE {table_name}"

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "message": f"Table '{table_name}' truncated"
    }


@tool(name="db_rename_table")
async def rename_table(
    connection_id: str,
    old_name: str,
    new_name: str,
) -> dict:
    """
    Rename a table.
    Requires user approval before execution.
    """
    # Create approval request
    request = gatekeeper.create_request("db_rename_table", {"old_name": old_name, "new_name": new_name, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    query = f"ALTER TABLE {old_name} RENAME TO {new_name}"

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "old_name": old_name,
        "new_name": new_name,
        "message": f"Table '{old_name}' renamed to '{new_name}'"
    }


@tool(name="db_add_foreign_key")
async def add_foreign_key(
    connection_id: str,
    table_name: str,
    constraint_name: str,
    column: str,
    ref_table: str,
    ref_column: str,
) -> dict:
    """
    Add a foreign key constraint to a table.
    Requires user approval before execution.
    """
    # Create approval request
    request = gatekeeper.create_request("db_add_foreign_key", {"table_name": table_name, "constraint_name": constraint_name, "connection_id": connection_id})

    # Wait for approval
    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    query = f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column})"

    result = DatabaseConnection.execute(connection_id, query)

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "connection_id": connection_id,
        "table": table_name,
        "constraint": constraint_name,
        "message": f"Foreign key '{constraint_name}' added: {table_name}.{column} → {ref_table}.{ref_column}"
    }
