## Framework Selection

For this lab I chose **FastAPI** as the Python web framework.

FastAPI provides automatic data validation, excellent async support, and
modern developer ergonomics while staying lightweight enough for a small
service like this lab. Compared to Flask and Django:

| Criteria          | FastAPI                     | Flask                      | Django                         |
|-------------------|-----------------------------|----------------------------|--------------------------------|
| Async support     | Built-in, first-class       | Extensions / manual setup  | Limited (ASGI via channels)   |
| Type hints        | First-class, Pydantic-based | Optional                   | Optional                      |
| Auto docs (OpenAPI)| Yes (Swagger & ReDoc)      | Via extensions             | Via DRF or third-party tools  |
| Learning curve    | Moderate                    | Very low                   | Higher (full framework)       |

FastAPI strikes a good balance between simplicity and modern features and is
well-suited for API-first services that will later be containerized and
monitored.

## Best Practices Applied

- **Clean code organization**
  - Separated helper functions for system, runtime, and request information:
    `get_system_info`, `get_runtime_info`, `get_request_info`, `get_endpoints`.
  - Clear module-level configuration (`HOST`, `PORT`, `DEBUG`, `START_TIME`).
- **PEP 8 compliance**
  - Used snake_case for functions and variables, upper-case for constants,
    and meaningful names for helpers and handlers.
- **Error handling**
  - Custom handler for `HTTPException` (including 404) returning JSON:
    ```python
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        ...
    ```
  - Fallback handler for unexpected exceptions returning a 500 error.
- **Logging**
  - Configured `logging.basicConfig` with timestamps and levels.
  - Logs on application startup and for each incoming request (method + path).
- **Pinned dependencies**
  - `fastapi==0.115.0`
  - `uvicorn[standard]==0.32.0`

## API Documentation

### `GET /`

- **Description**: Returns service, system, runtime, request, and endpoints
  information.
- **Example request**:

```bash
curl http://127.0.0.1:5000/
```

- **Example response (truncated)**:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "...",
    "platform": "Linux",
    "architecture": "x86_64",
    "python_version": "3.13.7"
  },
  "runtime": {
    "uptime_seconds": 10,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "...",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/...",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /health`

- **Description**: Health status of the service with current timestamp and uptime.
- **Example request**:

```bash
curl http://127.0.0.1:5000/health
```

- **Example response**:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T09:52:37.556677+00:00",
  "uptime_seconds": 17
}
```

## Testing Evidence

I tested the application locally using curl:

- Basic JSON output:
  ```bash
  source venv/bin/activate
  python app_python/app.py
  curl http://127.0.0.1:5000/
  curl http://127.0.0.1:5000/health
  ```
- Pretty-printed JSON:
  ```bash
  curl http://127.0.0.1:5000/ | jq
  curl http://127.0.0.1:5000/health | jq
  ```

Screenshots are saved under `app_python/docs/screenshots/`:

- `01-main-endpoint.png` – `/` endpoint full JSON.
- `02-health-check.png` – `/health` response.
- `03-formatted-output.png` – Pretty-printed JSON using `jq` or an API client.

## Challenges & Solutions

- **Choosing a framework**
  - Challenge: Balancing simplicity with future labs that need good API support.
  - Solution: Selected FastAPI for built-in OpenAPI, async support, and type
    hints.
- **Calculating uptime**
  - Challenge: Keeping an accurate runtime counter without external storage.
  - Solution: Store `START_TIME` at module load and compute deltas for each
    request.
- **Getting client information**
  - Challenge: Extract consistent client IP and user agent.
  - Solution: Use `request.client.host` and `request.headers.get("user-agent")`
    from FastAPI’s `Request`.
- **Environment-based configuration**
  - Challenge: Making host/port/debug configurable while keeping sensible
    defaults.
  - Solution: Read from `os.getenv` with defaults and document them clearly in
    the README.

## GitHub Community

Starring repositories helps maintainers measure interest, increases project
visibility, and lets me bookmark useful tools for later. Following professors,
TAs, and classmates exposes me to their work, supports collaboration on future
projects, and builds a professional network in the developer community.

