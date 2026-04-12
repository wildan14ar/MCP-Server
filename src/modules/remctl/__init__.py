"""
Remctl Module
Remote Control - Unified SSH session and tools management.

Usage:
    from src.routes import setup_remctl
    setup_remctl(app)  # ONE LINE!

    # Or import individually:
    from src.modules.remctl.config.session import RemctlSession
    from src.modules.remctl.config.tools import ToolsManager
"""

from .config.session import RemctlSession, SessionResult, SessionInfo
from .config.tools import ToolsManager
from .config.skills import SkillsManager

__all__ = [
    "RemctlSession",
    "SessionResult",
    "SessionInfo",
    "ToolsManager",
    "SkillsManager",
]
