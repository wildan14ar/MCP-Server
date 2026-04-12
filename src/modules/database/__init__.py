"""
Database Module
Database connection management and query execution via WebSocket + MCP tools.

Usage:
    from src.routes import setup_database
    setup_database(app)  # ONE LINE!

    # Or import individually:
    from src.modules.database.config.connection import DatabaseConnection
    from src.modules.database.config.tools import ToolsManager
"""

from .config.connection import DatabaseConnection, QueryResult, ConnectionInfo
from .config.tools import ToolsManager
from .config.skills import SkillsManager

__all__ = [
    "DatabaseConnection",
    "QueryResult",
    "ConnectionInfo",
    "ToolsManager",
    "SkillsManager",
]
