"""Test MCP Server using TestClient (no network)"""
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.routes import setup_remctl, setup_database

app = FastAPI()
setup_remctl(app)
setup_database(app)

client = TestClient(app)

print("=" * 50)
print("  MCP Server Test (TestClient)")
print("=" * 50)
print()

# Print all routes
print("Registered Routes:")
for r in app.routes:
    print(f"  {r.path} [{type(r).__name__}]")
print()

# Test HTTP endpoints
print("--- HTTP Tests ---")

# Test root
resp = client.get("/")
print(f"GET / -> {resp.status_code}")

# Test MCP SSE endpoints (should be 200 or method not allowed)
resp = client.get("/remctl/mcp")
print(f"GET /remctl/mcp -> {resp.status_code} [{resp.headers.get('content-type', 'N/A')}]")

resp = client.get("/database/mcp")
print(f"GET /database/mcp -> {resp.status_code} [{resp.headers.get('content-type', 'N/A')}]")

# Test WebSocket Remctl (expect SSH failure but WS flow OK)
print()
print("--- WebSocket Tests ---")

try:
    with client.websocket_connect("/remctl/ws") as ws:
        print("[REmCTL] WebSocket connected OK")
        # Use 127.0.0.1 with wrong port — will fail fast but WS stays alive
        ws.send_json({
            "type": "connect",
            "host": "127.0.0.1",
            "user": "test",
            "password": "test",
            "port": 65535,  # Invalid port, will fail but WS stays alive
        })
        resp = ws.receive_json()
        if resp.get("type") == "error":
            print(f"[REmCTL] SSH connect failed (expected): {resp.get('message')}")
            # Even if SSH fails, test that WS disconnect works
            ws.send_json({"type": "disconnect"})
        else:
            print(f"[REmCTL] Response: type={resp.get('type')}")
            ws.send_json({"type": "disconnect"})
        print("[REmCTL] Disconnect OK — no crash")
except Exception as e:
    print(f"[REmCTL] FAILED: {e}")

try:
    with client.websocket_connect("/database/ws") as ws:
        print("[DATABASE] WebSocket connected OK")
        ws.send_json({
            "type": "connect",
            "db_type": "sqlite",
            "database": ":memory:",
        })
        resp = ws.receive_json()
        print(f"[DATABASE] Response: type={resp.get('type')}, message={resp.get('message', resp.get('error', 'N/A'))}")
        ws.send_json({"type": "disconnect"})
except Exception as e:
    print(f"[DATABASE] FAILED: {e}")

print()
print("=" * 50)
print("  All tests completed")
print("=" * 50)
