"""
Skills Route
Exposes skill metadata from all modules as HTTP endpoints.

Endpoints:
- GET /skills        — List all available skills with metadata
- GET /skills/:name  — Get skill detail with available tools
"""

from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from src.modules.remctl.config.session import RemctlSession
from src.modules.database.config.connection import DatabaseConnection

# ─── Skill Metadata Definitions ──────────────────────────────────────────────

SKILLS_METADATA: Dict[str, Dict[str, Any]] = {
    "remote-server": {
        "id": "remote-server",
        "name": "Remote Server",
        "description": "Manage remote servers via SSH. Execute commands, manage files, monitor system health.",
        "icon": "terminal",
        "module": "remctl",
        "category": "Infrastructure",
        "credential_fields": ["host", "user", "password", "port"],
        "default_values": {
            "port": 22,
        },
        "tools_count": 29,
        "connection_class": RemctlSession,
    },
    "database": {
        "id": "database",
        "name": "Database",
        "description": "Connect to databases (PostgreSQL, MySQL, SQLite, MSSQL, Oracle). Run queries, inspect schemas, manage tables.",
        "icon": "database",
        "module": "database",
        "category": "Data",
        "credential_fields": ["db_type", "host", "user", "password", "database", "port"],
        "default_values": {
            "db_type": "postgresql",
            "port": 5432,
        },
        "tools_count": 33,
        "connection_class": DatabaseConnection,
    },
}


def _load_skill_content(module: str, skill_name: str) -> str | None:
    """Load skill markdown content if it exists."""
    skill_path = Path(__file__).parent.parent / "modules" / module / "skills" / f"{skill_name}.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return None


def _get_skill_status(skill_id: str) -> Dict[str, Any]:
    """Get connection status for a skill."""
    metadata = SKILLS_METADATA.get(skill_id)
    if not metadata:
        return {"status": "unknown", "message": "Skill not found"}

    module = metadata["module"]
    conn_class = metadata["connection_class"]

    # Check active sessions/connections
    if hasattr(conn_class, "_sessions"):
        # RemctlSession uses _sessions dict
        active = len(getattr(conn_class, "_sessions", {}))
        return {
            "status": "connected" if active > 0 else "disconnected",
            "active_sessions": active,
            "sessions": conn_class.list() if active > 0 else [],
        }
    elif hasattr(conn_class, "_connections"):
        # DatabaseConnection uses _connections dict
        active = len(getattr(conn_class, "_connections", {}))
        return {
            "status": "connected" if active > 0 else "disconnected",
            "active_sessions": active,
            "sessions": conn_class.list() if active > 0 else [],
        }

    return {"status": "disconnected", "active_sessions": 0}


def _get_skill_detail(skill_id: str) -> Dict[str, Any]:
    """Get detailed skill info including status and tools."""
    metadata = SKILLS_METADATA.get(skill_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")

    status = _get_skill_status(skill_id)

    # Load skill content from module
    content = _load_skill_content(metadata["module"], f"{metadata['module']}_management")
    if not content:
        # Try common skill names
        for name in [metadata["id"], metadata["name"].lower().replace(" ", "_")]:
            content = _load_skill_content(metadata["module"], name)
            if content:
                break

    return {
        "id": metadata["id"],
        "name": metadata["name"],
        "description": metadata["description"],
        "icon": metadata["icon"],
        "category": metadata["category"],
        "tools_count": metadata["tools_count"],
        "credential_fields": metadata["credential_fields"],
        "defaults": metadata["default_values"],
        "status": status["status"],
        "active_sessions": status.get("active_sessions", 0),
        "sessions": status.get("sessions", []),
        "documentation": content[:2000] if content else None,  # Truncate for API
    }


# ─── Router ──────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/")
def list_skills() -> Dict[str, Any]:
    """List all available skills with connection status."""
    skills = []
    for skill_id, metadata in SKILLS_METADATA.items():
        status = _get_skill_status(skill_id)
        skills.append({
            "id": skill_id,
            "name": metadata["name"],
            "description": metadata["description"],
            "icon": metadata["icon"],
            "category": metadata["category"],
            "tools_count": metadata["tools_count"],
            "status": status["status"],
            "active_sessions": status.get("active_sessions", 0),
        })

    return {
        "status": "success",
        "total": len(skills),
        "skills": skills,
    }


@router.get("/{skill_id}")
def get_skill(skill_id: str) -> Dict[str, Any]:
    """Get detailed skill information including status and documentation."""
    return {
        "status": "success",
        "skill": _get_skill_detail(skill_id),
    }


@router.get("/{skill_id}/status")
def get_skill_status(skill_id: str) -> Dict[str, Any]:
    """Get only connection status for a skill."""
    if skill_id not in SKILLS_METADATA:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")

    status = _get_skill_status(skill_id)
    return {
        "status": "success",
        "skill_id": skill_id,
        **status,
    }
