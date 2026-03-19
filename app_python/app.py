"""
DevOps Info Service - FastAPI implementation.

Provides system, runtime, and request information plus a basic health check.
Now emits structured JSON logs for easier aggregation.
"""

import json
import logging
import os
import platform
import socket
from time import perf_counter
from datetime import UTC, datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configuration
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", 5000))
DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


class JSONFormatter(logging.Formatter):
    """Format logs as JSON with common fields."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log_record: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        for attr in (
            "method",
            "path",
            "status_code",
            "client_ip",
            "duration",
        ):
            value = getattr(record, attr, None)
            if value is not None:
                log_record[attr] = value

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = [handler]
logger = logging.getLogger(__name__)


# Application start time for uptime calculations
START_TIME = datetime.now(UTC)


app = FastAPI(title="DevOps Info Service")


def normalize_endpoint(path: str) -> str:
    """Normalize endpoint labels to keep metric cardinality predictable."""
    if path in {"/", "/health", "/metrics"}:
        return path
    return "/other"


HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests processed by endpoint and status",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)
ENDPOINT_CALLS_TOTAL = Counter(
    "devops_info_endpoint_calls_total",
    "Total calls to user-facing API endpoints",
    ["endpoint"],
)
SYSTEM_INFO_COLLECTION_SECONDS = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log each HTTP request with structured JSON."""
    start = perf_counter()
    endpoint = normalize_endpoint(request.url.path)
    method = request.method
    status_code = 500

    HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = perf_counter() - start
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
        HTTP_REQUESTS_TOTAL.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(
            duration
        )

        logger.info(
            "HTTP request completed",
            extra={
                "method": method,
                "path": request.url.path,
                "status_code": status_code,
                "client_ip": request.client.host if request.client else None,
                "duration": duration,
            },
        )


def get_system_info() -> dict[str, Any]:
    """Collect system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_runtime_info() -> dict[str, Any]:
    """Calculate runtime information including uptime and current time."""
    now = datetime.now(UTC)
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


def get_request_info(request: Request) -> dict[str, Any]:
    """Extract request-related information."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.url.path,
    }


def get_endpoints() -> list[dict[str, str]]:
    """Describe available endpoints."""
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
    ]


@app.get("/")
async def index(request: Request) -> dict[str, Any]:
    """Main endpoint - service and system information."""
    logger.info(
        "Handling request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        },
    )

    ENDPOINT_CALLS_TOTAL.labels(endpoint="/").inc()
    with SYSTEM_INFO_COLLECTION_SECONDS.time():
        system_info = get_system_info()
    runtime_info = get_runtime_info()
    request_info = get_request_info(request)

    response: dict[str, Any] = {
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
async def health() -> dict[str, Any]:
    """Health check endpoint."""
    ENDPOINT_CALLS_TOTAL.labels(endpoint="/health").inc()
    runtime_info = get_runtime_info()
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "uptime_seconds": runtime_info["uptime_seconds"],
    }


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


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
    logger.info(
        "Starting DevOps Info Service",
        extra={"host": HOST, "port": PORT},
    )
    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG)
