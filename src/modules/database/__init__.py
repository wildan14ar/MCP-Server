"""
Database Module
Database connection management and query execution via WebSocket + MCP tools.

Usage:
    from src.modules.database import setup_database
    setup_database(app)  # ONE LINE!

    # Or import individually:
    from src.modules.database import database_app, mcp, register_tools
"""

from .config import DatabaseConnection, QueryResult, ConnectionInfo
from .config import ToolsManager, SkillsManager
from .main import database_app, mcp, database_router

__all__ = [
    "DatabaseConnection",
    "QueryResult",
    "ConnectionInfo",
    "ToolsManager",
    "SkillsManager",
    "database_app",
    "mcp",
    "database_router",
]
