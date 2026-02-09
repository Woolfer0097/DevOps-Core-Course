# DevOps Info Service (Python)

![Python CI](https://github.com/woolfer0097/DevOps-Core-Course/workflows/Python%20CI/badge.svg)
[![codecov](https://codecov.io/gh/woolfer0097/DevOps-Core-Course/branch/main/graph/badge.svg)](https://codecov.io/gh/woolfer0097/DevOps-Core-Course)

## Overview

The **DevOps Info Service** is a small FastAPI web application that exposes
basic system, runtime, and request information, plus a health check endpoint.
This service is the foundation for later labs (containerization, CI/CD,
monitoring, and persistence).

## Prerequisites

- Python 3.11+ installed (`python3 --version`)
- `venv` module available (`python3 -m venv --help`)
- Dependencies from `requirements.txt`:
  - `fastapi`
  - `uvicorn[standard]`

## Installation

Run these commands from the repo root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r app_python/requirements.txt
```

## Running the Application

From the repo root with the virtualenv activated:

```bash
python app_python/app.py
```

Run with custom configuration (host/port/debug via env vars):

```bash
HOST=127.0.0.1 PORT=8080 DEBUG=true python app_python/app.py
```

The service will start on `http://HOST:PORT` (default `0.0.0.0:5000`).

## API Endpoints

- `GET /`
  - **Description**: Returns service metadata, system information, runtime
    information, request details, and a list of available endpoints.
  - **Example**:
    ```bash
    curl http://127.0.0.1:5000/
    ```

- `GET /health`
  - **Description**: Simple health check with current timestamp and uptime.
  - **Example**:
    ```bash
    curl http://127.0.0.1:5000/health
    ```

## Configuration

The application is configurable via environment variables:

| Variable | Default     | Description                                 |
|----------|-------------|---------------------------------------------|
| `HOST`   | `0.0.0.0`   | Interface the server binds to               |
| `PORT`   | `5000`      | TCP port the server listens on              |
| `DEBUG`  | `False`     | Enables FastAPI/uvicorn reload when `true` |

Example:

```bash
HOST=127.0.0.1 PORT=3000 DEBUG=true python app_python/app.py
```

## Testing

The project uses **pytest** for unit testing with coverage tracking.

**Install development dependencies:**

```bash
pip install -r app_python/requirements-dev.txt
```

**Run all tests:**

```bash
cd app_python
pytest
```

**Run tests with coverage report:**

```bash
cd app_python
pytest --cov=. --cov-report=term-missing
```

**Run linter:**

```bash
cd app_python
ruff check .
```

**Test Coverage:** The project maintains >80% test coverage with comprehensive tests for all endpoints, error handling, and helper functions.

## Docker

**Build:** From `app_python/`, run `docker build -t <image-name> .`

**Run:** `docker run -p <host-port>:5000 <image-name>` (app listens on 5000 inside container)

**Pull from Docker Hub:** `docker pull <your-dockerhub-username>/<repo-name>:<tag>` then run as above.

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **Automated Testing:** Runs pytest with coverage on every push/PR
- **Code Quality:** Ruff linter enforces Python best practices
- **Security Scanning:** Semgrep checks for vulnerabilities (no cloud account required)
- **Docker Builds:** Multi-platform images (amd64/arm64) built and pushed to Docker Hub
- **Versioning:** Calendar versioning (YYYY.MM.DD) for clear deployment tracking

See [LAB03.md](docs/LAB03.md) for detailed CI/CD documentation.

**Required Secrets for CI:**
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub access token
- `CODECOV_TOKEN` - (Optional) Codecov token for coverage reports
