"""
Axiom REST API Server
Provides authenticated endpoints for mobile apps, web dashboards, and remote server management.
"""

import os
import secrets
import sys
from pathlib import Path
from typing import Any

from axiom.monitor.stats import SystemMonitor
from axiom.security.scanner import SecurityScanner
from axiom.users.manager import UserManager

try:
    import uvicorn
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.staticfiles import StaticFiles

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Axiom VPS Manager API", version="1.0.4", description="RESTful management endpoints for Axiom VPS Manager"
    )

    @app.middleware("http")
    async def response_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response

    def verify_token(x_api_key: str = Header(default="")):
        expected = os.environ.get("AXIOM_API_KEY", "")
        if len(expected) < 32:
            raise HTTPException(status_code=503, detail="Configure AXIOM_API_KEY with at least 32 characters")
        if not secrets.compare_digest(x_api_key.encode(), expected.encode()):
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
        try:
            return manager.create_user(username=username, days=days, limit=limit)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.delete("/api/v1/users/{username}", dependencies=[Depends(verify_token)])
    def delete_user(username: str) -> dict[str, str]:
        """Revokes and terminates a user account."""
        manager = UserManager()
        try:
            if manager.delete_user(username):
                return {"status": "success", "message": f"User {username} deleted"}
        except (ValueError, PermissionError) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        raise HTTPException(status_code=404, detail="User deletion failed")

    @app.get("/api/v1/security/audit", dependencies=[Depends(verify_token)])
    def security_audit() -> dict[str, Any]:
        """Performs a live security audit on the VPS."""
        return SecurityScanner.audit_system()

    for web_path in [Path(__file__).resolve().parents[3] / "web", Path(sys.prefix) / "share/axiom/web"]:
        if (web_path / "index.html").is_file():
            app.mount("/", StaticFiles(directory=web_path, html=True), name="dashboard")
            break


def start_api_server(host: str = "127.0.0.1", port: int = 8000):
    if len(os.environ.get("AXIOM_API_KEY", "")) < 32:
        raise RuntimeError("Set AXIOM_API_KEY to a random value of at least 32 characters before starting the API")
    if not FASTAPI_AVAILABLE:
        print("FastAPI / Uvicorn not installed. Run: pip install fastapi uvicorn")
        return
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_api_server()
