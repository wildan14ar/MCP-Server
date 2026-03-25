import sqlalchemy
from urllib.parse import quote_plus
from typing import List, Dict, Any, Optional


def get_db_engine(
    db_type: str,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    schema: str = None,
) -> sqlalchemy.Engine:
    """
    Create and return a SQLAlchemy engine.

    Args:
        db_type: Database type (postgresql, mysql, etc.)
        host: Database host
        port: Database port
        user: Database username
        password: Database password
        database: Database name
        schema: Schema name (optional, for PostgreSQL)

    Returns:
        SQLAlchemy Engine instance
    """
    # Build connection URL
    password_encoded = quote_plus(password)
    url = f"{db_type}://{user}:{password_encoded}@{host}:{port}/{database}"

    if schema and db_type == "postgresql":
        url += f"?options=-csearch_path%3D{schema}"

    engine = sqlalchemy.create_engine(url, echo=False)
    return engine


async def get_sql_schema(
    db_type: str,
    db_host: str,
    db_port: int,
    db_user: str,
    db_pass: str,
    db_name: str,
    table_name: str = None,
) -> str:
    """
    Get database schema information (tables and columns).

    Args:
        db_type: Database type (postgresql, mysql, etc.)
        db_host: Database host
        db_port: Database port
        db_user: Database username
        db_pass: Database password
        db_name: Database name
        table_name: Specific table name (optional, if None returns all tables)

    Returns:
        Schema information as formatted string
    """
    engine = get_db_engine(db_type, db_host, db_port, db_user, db_pass, db_name)
    
    schema_info = []
    
    with engine.connect() as conn:
        # Get all tables
        inspector = sqlalchemy.inspect(engine)
        tables = inspector.get_table_names()
        
        if table_name:
            tables = [t for t in tables if table_name.lower() in t.lower()]
        
        for table in tables:
            columns = inspector.get_columns(table)
            schema_info.append(f"\n📊 TABLE: {table}")
            schema_info.append("-" * 50)
            
            for col in columns:
                col_type = str(col.get("type", "UNKNOWN"))
                nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                primary = "🔑 PK" if col.get("primary_key", False) else ""
                default = col.get("default")
                default_str = f" DEFAULT {default}" if default else ""
                
                schema_info.append(f"  • {col['name']}: {col_type} {nullable}{primary}{default_str}")
            
            # Get foreign keys
            fkeys = inspector.get_foreign_keys(table)
            if fkeys:
                schema_info.append("  🔗 Foreign Keys:")
                for fk in fkeys:
                    fk_cols = ", ".join(fk.get("constrained_columns", []))
                    ref_table = fk.get("referred_table", "")
                    ref_cols = ", ".join(fk.get("referred_columns", []))
                    schema_info.append(f"    {fk_cols} → {ref_table}({ref_cols})")
            
            # Get indexes
            indexes = inspector.get_indexes(table)
            if indexes:
                schema_info.append("  📇 Indexes:")
                for idx in indexes:
                    idx_cols = ", ".join(idx.get("column_names", []))
                    unique = "UNIQUE " if idx.get("unique", False) else ""
                    schema_info.append(f"    {unique}INDEX: {idx.get('name', 'unknown')}({idx_cols})")
    
    return "\n".join(schema_info) if schema_info else "No tables found."


async def execute_sql_query(
    db_type: str,
    db_host: str,
    db_port: int,
    db_user: str,
    db_pass: str,
    db_name: str,
    query: str,
    schema: str = None,
) -> Dict[str, Any]:
    """
    Execute SQL query and return structured results.

    Args:
        db_type: Database type (postgresql, mysql, etc.)
        db_host: Database host
        db_port: Database port
        db_user: Database username
        db_pass: Database password
        db_name: Database name
        query: SQL query to execute
        schema: Schema name (optional)

    Returns:
        Dictionary with columns, rows, and row count
    """
    engine = get_db_engine(db_type, db_host, db_port, db_user, db_pass, db_name, schema)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(query))
            
            # Get column names
            columns = list(result.keys()) if hasattr(result, 'keys') else []
            
            # Fetch all rows
            rows = result.fetchall()
            
            # Convert to list of dicts
            rows_dict = [dict(row._mapping) for row in rows]
            
            return {
                "success": True,
                "columns": columns,
                "row_count": len(rows),
                "data": rows_dict,
                "preview": str(rows_dict[:10]) if len(rows) > 10 else str(rows_dict),
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
        }
