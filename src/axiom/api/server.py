"""
Axiom REST API Server
Provides authenticated endpoints for mobile apps, web dashboards, and remote server management.
"""

from typing import Any

from axiom.monitor.stats import SystemMonitor
from axiom.security.scanner import SecurityScanner
from axiom.users.manager import UserManager

try:
    import uvicorn
    from fastapi import Depends, FastAPI, Header, HTTPException

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Axiom VPS Manager API", version="1.0.0", description="RESTful management endpoints for Axiom VPS Manager"
    )

    API_SECRET_TOKEN = "axiom_secure_token"

    def verify_token(x_api_key: str = Header(...)):
        if x_api_key != API_SECRET_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key")
        return x_api_key

    @app.get("/api/v1/status", dependencies=[Depends(verify_token)])
    def get_status() -> dict[str, Any]:
        """Returns live system telemetry and health metrics."""
        return SystemMonitor.get_system_metrics()

    @app.get("/api/v1/users", dependencies=[Depends(verify_token)])
    def list_users() -> list[dict[str, str]]:
        """Returns all managed user accounts."""
        manager = UserManager()
        return manager.list_users()

    @app.post("/api/v1/users", dependencies=[Depends(verify_token)])
    def create_user(username: str, days: int = 30, limit: int = 1) -> dict[str, str]:
        """Provisions a new user account."""
        manager = UserManager()
        return manager.create_user(username=username, days=days, limit=limit)

    @app.delete("/api/v1/users/{username}", dependencies=[Depends(verify_token)])
    def delete_user(username: str) -> dict[str, str]:
        """Revokes and terminates a user account."""
        manager = UserManager()
        if manager.delete_user(username):
            return {"status": "success", "message": f"User {username} deleted"}
        raise HTTPException(status_code=404, detail="User deletion failed")

    @app.get("/api/v1/security/audit", dependencies=[Depends(verify_token)])
    def security_audit() -> dict[str, Any]:
        """Performs a live security audit on the VPS."""
        return SecurityScanner.audit_system()


def start_api_server(host: str = "127.0.0.1", port: int = 8000):
    if not FASTAPI_AVAILABLE:
        print("FastAPI / Uvicorn not installed. Run: pip install fastapi uvicorn")
        return
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_api_server()
