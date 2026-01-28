## Implementation Overview

The Go implementation of the **DevOps Info Service** mirrors the Python
FastAPI version. It uses the standard `net/http` package and exposes:

- `GET /` – service, system, runtime, request, and endpoints information.
- `GET /health` – basic health status with uptime and timestamp.

Core pieces:

- Structs for `Service`, `System`, `RuntimeInfo`, `RequestInfo`, `Endpoint`,
  and `ServiceInfo`.
- A global `startTime` used to compute uptime.
- Helper functions for system info, runtime info, request info, and endpoints.

## Build and Run

From the `app_go` directory:

```bash
go run .
```

or:

```bash
go build -o devops-info-service-go
./devops-info-service-go
```

The server listens on `HOST:PORT` (default `0.0.0.0:8080`).

## API Examples

### `GET /`

```bash
curl http://127.0.0.1:8080/
```

Example (truncated) JSON:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service (Go)",
    "framework": "net/http"
  },
  "system": {
    "hostname": "...",
    "platform": "linux",
    "architecture": "amd64",
    "cpu_count": 12,
    "go_version": "go1.25.5"
  },
  "runtime": {
    "uptime_seconds": 11,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "...",
    "timezone": "UTC"
  }
}
```

### `GET /health`

```bash
curl http://127.0.0.1:8080/health
```

Example response:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T09:57:50.21785182Z",
  "uptime_seconds": 25
}
```

## Binary Size Comparison

Example comparison (exact sizes will vary by machine and compiler version):

- Python app: source files only; runtime provided by Python + dependencies.
- Go app: single compiled binary `devops-info-service-go` (e.g. a few MB).

To inspect the Go binary size:

```bash
cd app_go
go build -o devops-info-service-go
ls -lh devops-info-service-go
```

## Screenshots

Save Go-specific screenshots under `app_go/docs/screenshots/`:

- `go-build.png` – Output of `go build` or `go run .` in the terminal.
- `go-main-endpoint.png` – `/` JSON response (browser, curl, or HTTP client).
- `go-health-endpoint.png` – `/health` JSON response.

