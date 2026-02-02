## Overview

The Go version of the **DevOps Info Service** mirrors the Python FastAPI
application. It exposes two endpoints:

- `GET /` – service, system, runtime, and request information
- `GET /health` – simple health check with uptime

This implementation is used as a bonus task to compare a compiled binary
to the Python version and prepare for multi-stage Docker builds.

## Prerequisites

- Go 1.22+ installed (`go version`)

## Build and Run

From the `app_go` directory:

```bash
go run .
```

Or build a binary and run it:

```bash
go build -o devops-info-service-go
./devops-info-service-go
```

By default the service listens on `0.0.0.0:8080`.

### Configuration

Environment variables:

| Variable | Default   | Description                    |
|----------|-----------|--------------------------------|
| `HOST`   | `0.0.0.0` | Interface to bind              |
| `PORT`   | `8080`    | TCP port for HTTP server       |

Example:

```bash
HOST=127.0.0.1 PORT=9090 go run .
```

## API Endpoints

- `GET /`
  - **Description**: Returns service metadata, system details, runtime info,
    request information, and an endpoints list.
- `GET /health`
  - **Description**: Returns a basic health status with timestamp and uptime.

