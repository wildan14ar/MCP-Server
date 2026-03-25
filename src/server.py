"""
Main Server - Remctl MCP Server

Run with:
    python -m src.server

Endpoints:
- WebSocket: ws://localhost:8017/remctl/ws
- MCP:       POST http://localhost:8017/remctl/mcp
"""

from fastapi import FastAPI
import uvicorn

from src.modules.remctl import remctl_router


def main():
    """Create and run Remctl MCP Server."""

    # Create FastAPI app
    app = FastAPI(title="Remctl MCP Server", version="1.0.0")
    app.include_router(remctl_router)

    print("🚀 Remctl MCP Server")
    print()
    print("Endpoints:")
    print("  WebSocket: ws://localhost:8017/remctl/ws")
    print("  MCP:       POST http://localhost:8017/remctl/mcp")
    print()
    print("Starting server on http://localhost:8017")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8017)


if __name__ == "__main__":
    main()
