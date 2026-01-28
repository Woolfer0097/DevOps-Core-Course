"""
DevOps Info Service - FastAPI implementation.

Provides system, runtime, and request information plus a basic health check.
"""

import logging
import os
import platform
import socket
from datetime import datetime, timezone
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


# Configuration
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", 5000))
DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Application start time for uptime calculations
START_TIME = datetime.now(timezone.utc)


app = FastAPI(title="DevOps Info Service")


def get_system_info() -> Dict[str, Any]:
    """Collect system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_runtime_info() -> Dict[str, Any]:
    """Calculate runtime information including uptime and current time."""
    now = datetime.now(timezone.utc)
    delta = now - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return {
        "uptime_seconds": seconds,
        "uptime_human": f"{hours} hour{'s' if hours != 1 else ''}, "
        f"{minutes} minute{'s' if minutes != 1 else ''}",
        "current_time": now.isoformat(),
        "timezone": "UTC",
    }


def get_request_info(request: Request) -> Dict[str, Any]:
    """Extract request-related information."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.url.path,
    }


def get_endpoints() -> List[Dict[str, str]]:
    """Describe available endpoints."""
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


@app.get("/")
async def index(request: Request) -> Dict[str, Any]:
    """Main endpoint - service and system information."""
    logger.info("Handling request for %s %s", request.method, request.url.path)

    system_info = get_system_info()
    runtime_info = get_runtime_info()
    request_info = get_request_info(request)

    response: Dict[str, Any] = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": system_info,
        "runtime": runtime_info,
        "request": request_info,
        "endpoints": get_endpoints(),
    }
    return response


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    runtime_info = get_runtime_info()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": runtime_info["uptime_seconds"],
    }


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle HTTP exceptions like 404."""
    logger.warning(
        "HTTP error %s on %s %s", exc.status_code, request.method, request.url.path
    )

    if exc.status_code == 404:
        payload = {
            "error": "Not Found",
            "message": "Endpoint does not exist",
        }
    else:
        payload = {
            "error": "HTTP Error",
            "message": exc.detail,
        }

    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unexpected errors."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    payload = {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }
    return JSONResponse(status_code=500, content=payload)


if __name__ == "__main__":
    logger.info("Starting DevOps Info Service on %s:%s", HOST, PORT)
    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG)
