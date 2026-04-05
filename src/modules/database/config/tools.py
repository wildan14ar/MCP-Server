"""
Tools Manager - Class-based tool registry with auto-discovery.
Auto-discovers all tool modules and registers them to MCP.

Usage:
    from src.modules.database.config.tools import ToolsManager

    mcp = FastMCP('my-server')
    tools = ToolsManager()
    tools.get_tools(mcp)  # Auto-discovers and registers all tools
"""

import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Any, Callable
from mcp.server.fastmcp import FastMCP

# Global tool registry
_tools_registry: List[Dict[str, Any]] = []


def tool(name: str = None, description: str = None):
    """
    Decorator to mark a function as an MCP tool.
    Auto-hides database config params: db_type, host, port, user, password, database, schema
    """
    CONFIG_PARAMS = {'db_type', 'host', 'port', 'user', 'password', 'database', 'schema', 'connection_id', 'token'}

    def decorator(func: Callable):
        sig = inspect.signature(func)

        # Filter out config params
        new_params = [
            param for param in sig.parameters.values()
            if param.name not in CONFIG_PARAMS
        ]

        async def wrapper(**kwargs):
            return await func(**kwargs)

        wrapper.__signature__ = sig.replace(parameters=new_params)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__

        _tools_registry.append({
            "name": name or func.__name__,
            "description": description or (func.__doc__ or "").strip(),
            "func": wrapper,
        })
        return wrapper

    return decorator


def _register_all_tools(mcp: FastMCP) -> int:
    """Register all tools in registry to MCP server."""
    for tool_info in _tools_registry:
        mcp.tool(name=tool_info["name"])(tool_info["func"])
    return len(_tools_registry)


class ToolsManager:
    """
    Manages MCP tools with auto-discovery.

    Usage:
        from src.modules.database.config.tools import ToolsManager

        mcp = FastMCP('my-server')
        tools = ToolsManager()
        tools.get_tools(mcp)  # Auto-discovers and registers all tools
    """

    def __init__(self):
        self._tools_path = Path(__file__).parent.parent / "tools"

    def get_tools_path(self) -> Path:
        """Get tools directory."""
        return self._tools_path

    def discover_tool_modules(self) -> List[str]:
        """Discover all tool module files."""
        return [f.stem for f in self._tools_path.glob("*.py") if not f.stem.startswith("_")]

    def auto_discover_tools(self):
        """Auto-discover and load all tool modules."""
        for module_name in self.discover_tool_modules():
            module_path = f"src.modules.database.tools.{module_name}"
            try:
                importlib.import_module(module_path)
            except Exception as e:
                print(f"Warning: Failed to load {module_name}: {e}")

    def get_tools(self, mcp: FastMCP) -> int:
        """
        Auto-discover and register all tools to MCP server.

        Returns:
            Number of tools registered
        """
        # Auto-discover all tool modules
        self.auto_discover_tools()

        # Register all discovered tools to MCP
        return _register_all_tools(mcp)
