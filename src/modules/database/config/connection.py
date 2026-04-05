"""
DatabaseConnection - Unified database connection manager.
Single class for creating, managing, and executing queries on databases.

Features:
- Create multiple connections (credentials stored automatically)
- Execute queries by connection ID (no credentials needed!)
- List connections, get info, close connections
- Transaction management (commit/rollback)
- Schema inspection helpers
- Query result caching

Usage:
    # Create connection (credentials stored automatically)
    conn_id = DatabaseConnection.create(
        db_type="postgresql",
        host="localhost",
        port=5432,
        user="admin",
        password="secret",
        database="mydb"
    )

    # Execute (NO credentials - auto from stored connection!)
    result = DatabaseConnection.execute(conn_id, "SELECT * FROM users")

    # List all connections
    connections = DatabaseConnection.list()

    # Get connection info
    info = DatabaseConnection.info(conn_id)
"""

import time
import uuid
import secrets
import hashlib
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool


@dataclass
class QueryResult:
    """Result of a query execution."""
    success: bool
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time: float
    connection_id: str
    error: Optional[str] = None


@dataclass
class ConnectionInfo:
    """Connection metadata."""
    connection_id: str
    token: str
    db_type: str
    host: str
    port: int
    database: str
    user: str
    created_at: str
    is_active: bool
    query_count: int


class DatabaseConnection:
    """
    Unified Database Connection Manager

    Class Methods (for multi-connection):
        DatabaseConnection.create(db_type, host, user, password) → connection_id
        DatabaseConnection.list() → all connections
        DatabaseConnection.info(connection_id) → connection info
        DatabaseConnection.execute(connection_id, query) → result
        DatabaseConnection.close(connection_id) → close

    Instance Methods (for single connection):
        conn = DatabaseConnection(db_type, host, user, password)
        conn.connect()
        conn.execute("SELECT * FROM users")
        conn.close()
    """

    # Class-level connection storage (shared across all instances)
    _connections: Dict[str, 'DatabaseConnection'] = {}
    _info: Dict[str, ConnectionInfo] = {}
    _engines: Dict[str, Engine] = {}

    # Query result cache
    _query_cache: Dict[str, Any] = {}
    _cache_ttl: int = 300  # 5 minutes

    # Instance attributes
    def __init__(
        self,
        db_type: str,
        host: str,
        user: str,
        password: Optional[str] = None,
        database: str = "",
        port: int = 5432,
        schema: Optional[str] = None,
        pool_size: int = 5,
        echo: bool = False,
    ):
        self.db_type = db_type.lower()
        self.host = host
        self.user = user
        self.password = password or ""
        self.database = database
        self.port = port
        self.schema = schema
        self.pool_size = pool_size
        self.echo = echo

        self.connection_id = str(uuid.uuid4())[:8]
        self.token = secrets.token_urlsafe(32)

        self.engine: Optional[Engine] = None
        self._connected = False
        self._transaction_active = False
        self._transaction_conn = None
        self.query_count = 0
        self.audit_events: List[dict] = []

    def _audit(self, event: str, data: str = ""):
        """Record audit event."""
        self.audit_events.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "connection": self.connection_id,
            "event": event,
            "data": data[:200],  # Limit data length
        })

    def _build_connection_string(self) -> str:
        """Build database connection URL."""
        from urllib.parse import quote_plus

        password_encoded = quote_plus(self.password)

        if self.db_type == "postgresql":
            url = f"postgresql://{self.user}:{password_encoded}@{self.host}:{self.port}/{self.database}"
            if self.schema:
                url += f"?options=-csearch_path%3D{self.schema}"
        elif self.db_type == "mysql":
            url = f"mysql+pymysql://{self.user}:{password_encoded}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == "sqlite":
            url = f"sqlite:///{self.database if self.database else ':memory:'}"
        elif self.db_type == "mssql":
            url = f"mssql+pyodbc://{self.user}:{password_encoded}@{self.host}:{self.port}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server"
        elif self.db_type == "oracle":
            url = f"oracle+cx_oracle://{self.user}:{password_encoded}@{self.host}:{self.port}/?service_name={self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

        return url

    def connect(self):
        """Establish database connection."""
        self._audit("CONNECT")

        try:
            conn_str = self._build_connection_string()

            # Use StaticPool for SQLite to keep it in memory
            if self.db_type == "sqlite":
                self.engine = create_engine(
                    conn_str,
                    echo=self.echo,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                )
            else:
                self.engine = create_engine(
                    conn_str,
                    echo=self.echo,
                    pool_pre_ping=True,
                    pool_size=self.pool_size,
                )

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            self._connected = True
            self._audit("CONNECTED")

        except SQLAlchemyError as e:
            self._audit("CONNECT_FAILED", str(e))
            raise ConnectionError(f"Failed to connect to database: {e}")

    def is_connected(self) -> bool:
        """Check if connected."""
        if not self._connected or self.engine is None:
            return False

        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def execute(self, query: str, params: Optional[Dict] = None, timeout: int = 30) -> QueryResult:
        """
        Execute a SQL query.

        Args:
            query: SQL query to execute
            params: Query parameters (for parameterized queries)
            timeout: Query timeout in seconds

        Returns:
            QueryResult with columns, rows, and metadata
        """
        if not self._connected:
            raise RuntimeError("Not connected to database")

        self._audit("QUERY", query)
        start_time = time.time()

        try:
            # Check cache for SELECT queries
            cache_key = None
            if query.strip().upper().startswith("SELECT"):
                cache_key = hashlib.md5(f"{self.connection_id}:{query}:{str(params)}".encode()).hexdigest()
                if cache_key in self._query_cache:
                    cached_time, cached_result = self._query_cache[cache_key]
                    if time.time() - cached_time < self._cache_ttl:
                        self._audit("CACHE_HIT", query)
                        return cached_result

            # Execute query
            if self._transaction_active and self._transaction_conn:
                conn = self._transaction_conn
                result = conn.execute(text(query), params or {})
            else:
                with self.engine.connect() as conn:
                    result = conn.execute(text(query), params or {})

            # Get column names
            columns = list(result.keys()) if hasattr(result, 'keys') else []

            # Fetch all rows
            rows = result.fetchall()

            # Convert to list of dicts
            rows_dict = []
            for row in rows:
                row_data = {}
                for key, value in dict(row._mapping).items():
                    # Handle datetime and other non-serializable types
                    if hasattr(value, 'isoformat'):
                        row_data[key] = value.isoformat()
                    else:
                        row_data[key] = value
                rows_dict.append(row_data)

            execution_time = time.time() - start_time

            query_result = QueryResult(
                success=True,
                columns=columns,
                rows=rows_dict,
                row_count=len(rows_dict),
                execution_time=execution_time,
                connection_id=self.connection_id,
            )

            # Cache SELECT queries
            if cache_key:
                self._query_cache[cache_key] = (time.time(), query_result)

            self.query_count += 1
            self._audit("QUERY_SUCCESS", f"{len(rows_dict)} rows in {execution_time:.2f}s")

            return query_result

        except SQLAlchemyError as e:
            execution_time = time.time() - start_time
            self._audit("QUERY_FAILED", str(e))

            return QueryResult(
                success=False,
                columns=[],
                rows=[],
                row_count=0,
                execution_time=execution_time,
                connection_id=self.connection_id,
                error=str(e),
            )

    def execute_many(self, query: str, params_list: List[Dict], batch_size: int = 1000) -> QueryResult:
        """
        Execute a SQL query with multiple parameter sets.

        Args:
            query: SQL query to execute
            params_list: List of parameter dictionaries
            batch_size: Batch size for execution

        Returns:
            QueryResult with execution metadata
        """
        if not self._connected:
            raise RuntimeError("Not connected to database")

        self._audit("EXECUTE_MANY", query)
        start_time = time.time()
        total_affected = 0

        try:
            with self.engine.connect() as conn:
                for i in range(0, len(params_list), batch_size):
                    batch = params_list[i:i + batch_size]
                    result = conn.execute(text(query), batch)
                    total_affected += result.rowcount if result.rowcount else 0
                conn.commit()

            execution_time = time.time() - start_time
            self.query_count += 1
            self._audit("EXECUTE_MANY_SUCCESS", f"{total_affected} rows affected")

            return QueryResult(
                success=True,
                columns=["affected_rows"],
                rows=[{"affected_rows": total_affected}],
                row_count=1,
                execution_time=execution_time,
                connection_id=self.connection_id,
            )

        except SQLAlchemyError as e:
            execution_time = time.time() - start_time
            self._audit("EXECUTE_MANY_FAILED", str(e))

            return QueryResult(
                success=False,
                columns=[],
                rows=[],
                row_count=0,
                execution_time=execution_time,
                connection_id=self.connection_id,
                error=str(e),
            )

    def begin_transaction(self):
        """Begin a database transaction."""
        if self._transaction_active:
            raise RuntimeError("Transaction already active")

        self._transaction_conn = self.engine.connect()
        self._transaction_active = True
        self._audit("TRANSACTION_BEGIN")

    def commit_transaction(self):
        """Commit the current transaction."""
        if not self._transaction_active:
            raise RuntimeError("No active transaction")

        self._transaction_conn.commit()
        self._transaction_active = False
        self._transaction_conn.close()
        self._transaction_conn = None
        self._audit("TRANSACTION_COMMIT")

    def rollback_transaction(self):
        """Rollback the current transaction."""
        if not self._transaction_active:
            raise RuntimeError("No active transaction")

        self._transaction_conn.rollback()
        self._transaction_active = False
        self._transaction_conn.close()
        self._transaction_conn = None
        self._audit("TRANSACTION_ROLLBACK")

    def get_schema_info(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get database schema information.

        Args:
            table_name: Specific table name (optional)

        Returns:
            Dictionary with schema information
        """
        if not self._connected:
            raise RuntimeError("Not connected to database")

        inspector = inspect(self.engine)
        tables = inspector.get_table_names()

        if table_name:
            tables = [t for t in tables if table_name.lower() in t.lower()]

        schema = {}
        for table in tables:
            columns = inspector.get_columns(table)
            pk_cols = [col['name'] for col in columns if col.get('primary_key')]
            fk_list = inspector.get_foreign_keys(table)
            indexes = inspector.get_indexes(table)

            schema[table] = {
                "columns": [
                    {
                        "name": col['name'],
                        "type": str(col['type']),
                        "nullable": col.get('nullable', True),
                        "primary_key": col.get('primary_key', False),
                        "default": str(col.get('default')) if col.get('default') else None,
                    }
                    for col in columns
                ],
                "primary_key": pk_cols,
                "foreign_keys": [
                    {
                        "constrained_columns": fk.get('constrained_columns', []),
                        "referred_table": fk.get('referred_table', ''),
                        "referred_columns": fk.get('referred_columns', []),
                    }
                    for fk in fk_list
                ],
                "indexes": [
                    {
                        "name": idx.get('name', 'unknown'),
                        "columns": idx.get('column_names', []),
                        "unique": idx.get('unique', False),
                    }
                    for idx in indexes
                ],
            }

        return schema

    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table."""
        query = f"SELECT COUNT(*) as cnt FROM {table_name}"
        result = self.execute(query)
        if result.success and result.rows:
            return result.rows[0].get('cnt', 0)
        return 0

    def clear_cache(self):
        """Clear query cache."""
        self._query_cache.clear()
        self._audit("CACHE_CLEARED")

    def close(self):
        """Close database connection."""
        self._audit("CLOSE")
        self._connected = False

        if self._transaction_active and self._transaction_conn:
            try:
                self._transaction_conn.rollback()
            except Exception:
                pass
            self._transaction_conn.close()
            self._transaction_conn = None
            self._transaction_active = False

        if self.engine:
            self.engine.dispose()

        # Remove from cache
        keys_to_remove = [k for k, v in self._query_cache.items()
                         if v[1].connection_id == self.connection_id]
        for k in keys_to_remove:
            del self._query_cache[k]

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    # ============ CLASS METHODS (Multi-Connection Management) ============

    @classmethod
    def create(
        cls,
        db_type: str,
        host: str,
        user: str,
        password: Optional[str] = None,
        database: str = "",
        port: int = 5432,
        schema: Optional[str] = None,
    ) -> str:
        """
        Create new database connection.

        Args:
            db_type: Database type (postgresql, mysql, sqlite, mssql, oracle)
            host: Database host
            user: Username
            password: Password (optional for SQLite)
            database: Database name
            port: Database port (default: 5432 for PostgreSQL)
            schema: Schema name (optional, for PostgreSQL)

        Returns:
            Connection ID
        """
        conn = cls(
            db_type=db_type,
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            schema=schema,
        )
        conn.connect()

        cid = conn.connection_id
        cls._connections[cid] = conn
        cls._info[cid] = ConnectionInfo(
            connection_id=cid,
            token=conn.token,
            db_type=db_type,
            host=host,
            port=port,
            database=database,
            user=user,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_active=True,
            query_count=0,
        )
        return cid

    @classmethod
    def list(cls) -> List[Dict]:
        """List all active connections."""
        return [asdict(info) for info in cls._info.values()]

    @classmethod
    def info(cls, connection_id: str) -> Dict:
        """Get connection info."""
        info = cls._info.get(connection_id)
        if not info:
            return {"status": "error", "message": "Connection not found"}

        conn = cls._connections.get(connection_id)
        return {
            "status": "success",
            "connection": asdict(info),
            "is_connected": conn.is_connected() if conn else False,
            "queries_executed": conn.query_count if conn else 0,
            "recent_events": conn.audit_events[-5:] if conn else [],
        }

    @classmethod
    def execute(cls, connection_id: str, query: str, params: Optional[Dict] = None, timeout: int = 30) -> Dict:
        """
        Execute query in connection (only connection_id needed!).

        Args:
            connection_id: Connection ID (from create())
            query: SQL query to execute
            params: Query parameters
            timeout: Query timeout

        Returns:
            Query result
        """
        conn = cls._connections.get(connection_id)
        if not conn:
            return {
                "status": "error",
                "message": f"Connection '{connection_id}' not found",
                "available": list(cls._connections.keys())
            }

        if not conn.is_connected():
            return {"status": "error", "message": "Connection not active"}

        try:
            result = conn.execute(query, params, timeout)
            return {
                "status": "success",
                "connection_id": connection_id,
                "query": query,
                "success": result.success,
                "columns": result.columns,
                "rows": result.rows,
                "row_count": result.row_count,
                "execution_time": result.execution_time,
                "error": result.error,
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "connection_id": connection_id}

    @classmethod
    def get_schema(cls, connection_id: str, table_name: Optional[str] = None) -> Dict:
        """Get schema information for connection."""
        conn = cls._connections.get(connection_id)
        if not conn:
            return {"status": "error", "message": "Connection not found"}

        try:
            schema = conn.get_schema_info(table_name)
            return {
                "status": "success",
                "connection_id": connection_id,
                "schema": schema,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @classmethod
    def close(cls, connection_id: str) -> bool:
        """Close connection."""
        conn = cls._connections.pop(connection_id, None)
        if conn:
            cls._info.pop(connection_id, None)
            conn.close()
            return True
        return False

    @classmethod
    def close_all(cls):
        """Close all connections."""
        for c in cls._connections.values():
            c.close()
        cls._connections.clear()
        cls._info.clear()
        cls._query_cache.clear()
