"""
Remctl Module
Remote Control - Unified SSH session and tools management.

Usage:
    from src.modules.remctl import setup_remctl
    setup_remctl(app)  # ONE LINE!
    
    # Or import individually:
    from src.modules.remctl import remctl_app, mcp, register_tools
"""

from .config import RemctlSession, SessionResult, SessionInfo
from .config import ToolsManager, SkillsManager
from .main import remctl_app, mcp, register_tools, setup_remctl

__all__ = [
    "RemctlSession",
    "SessionResult",
    "SessionInfo",
    "ToolsManager",
    "SkillsManager",
    "remctl_app",
    "mcp",
    "register_tools",
    "setup_remctl",
]
