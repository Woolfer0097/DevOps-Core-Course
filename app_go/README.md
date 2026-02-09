# DevOps Info Service (Go)

![Go CI](https://github.com/woolfer0097/DevOps-Core-Course/workflows/Go%20CI/badge.svg)
[![codecov](https://codecov.io/gh/woolfer0097/DevOps-Core-Course/branch/main/graph/badge.svg?flag=go-unittests)](https://codecov.io/gh/woolfer0097/DevOps-Core-Course)

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

## Testing

The project includes comprehensive unit tests with 76%+ coverage.

**Run all tests:**

```bash
cd app_go
go test -v ./...
```

**Run tests with coverage report:**

```bash
cd app_go
go test -v -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out  # View in browser
```

**Run linter:**

```bash
cd app_go
golangci-lint run
```

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **Automated Testing:** Runs go test with coverage on every push/PR
- **Code Quality:** golangci-lint enforces Go best practices
- **Security Scanning:** Semgrep checks for vulnerabilities (no cloud account required)
- **Docker Builds:** Multi-platform images (amd64/arm64) built and pushed to Docker Hub
- **Versioning:** Calendar versioning (YYYY.MM.DD) for clear deployment tracking
- **Path Filters:** Only runs when Go app files change (efficient CI)

See [LAB03.md](docs/LAB03.md) for detailed CI/CD documentation.

**Required Secrets for CI:**
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub access token
- `CODECOV_TOKEN` - (Optional) Codecov token for coverage reports

