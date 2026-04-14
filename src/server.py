"""
Main Server - MCP Server with Modular Routes

Run with:
    python -m src.server

Endpoints:
- Skills:
    REST:      http://localhost:8017/skills
    Detail:    http://localhost:8017/skills/{skill_id}

- Remctl:
    WebSocket: ws://localhost:8017/remctl/ws
    MCP:       http://localhost:8017/remctl/mcp

- Database:
    WebSocket: ws://localhost:8017/database/ws
    MCP:       http://localhost:8017/database/mcp
"""

from fastapi import FastAPI
import uvicorn

from src.routes import setup_remctl, setup_database
from src.routes.skills import router as skills_router


def main():
    """Create and run MCP Server."""

    # Create FastAPI app
    app = FastAPI(title="MCP Server", version="1.0.0")

    # Setup routes
    setup_remctl(app)
    setup_database(app)
    app.include_router(skills_router)

    print("🚀 MCP Server")
    print()
    print("Skills:")
    print("  REST:      http://localhost:8017/skills")
    print()
    print("Remctl:")
    print("  WebSocket: ws://localhost:8017/remctl/ws")
    print("  MCP:       http://localhost:8017/remctl/mcp")
    print()
    print("Database:")
    print("  WebSocket: ws://localhost:8017/database/ws")
    print("  MCP:       http://localhost:8017/database/mcp")
    print()
    print("Starting server on http://localhost:8017")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8017)


if __name__ == "__main__":
    main()
