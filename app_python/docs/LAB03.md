# Lab 3 — CI/CD Implementation

## Overview

**Testing Framework:** pytest (chosen for excellent fixture support, clear assertions, and comprehensive plugin ecosystem)

**Endpoints Covered:**
- `GET /` - System and service information endpoint
- `GET /health` - Health check endpoint
- Error handling (404, 405)

**Versioning Strategy:** Calendar Versioning (CalVer) - `YYYY.MM.DD` format
- **Rationale:** Better for continuous deployment, easy to understand when a version was released, no need to determine breaking changes

**CI Trigger Configuration:**
- Runs on push to `main`, `master`, `lab03` branches
- Runs on pull requests to `main`, `master`
- Only triggers when `app_python/` files or workflow file changes (path filters)

## Workflow Evidence

**Workflow Structure:**
```
test → Runs linting (Ruff) and unit tests with coverage
security → Semgrep security scanning
docker → Builds and pushes Docker images (depends on test + security)
```

**Local Testing:**
```bash
cd app_python
pip install -r requirements-dev.txt
pytest
```

**Docker Images:** `woolfer0097/devops-info-python`
- Tags: `2026.02`, `2026.02.09`, `latest`, `2026.02.09-<sha>`

**Status Badge:** See README.md

## Best Practices Implemented

1. **Dependency Caching:** `actions/setup-python` with pip cache - reduces install time by ~30-50 seconds on cache hits
2. **Job Dependencies:** Docker build only runs if tests and security checks pass
3. **Path Filters:** Workflow only runs when Python app files change, saving CI minutes
4. **Multi-platform Builds:** Docker images built for amd64 and arm64 architectures
5. **Docker Layer Caching:** GitHub Actions cache reduces build time by ~40%
6. **Conditional Push:** Docker push only happens on push events, not PRs
7. **Security Scanning (Semgrep):** Scans for security vulnerabilities, misconfigurations, and code quality issues

### Semgrep Integration

**Configuration:** Running multiple rulesets:
- `p/security-audit` - Security vulnerabilities
- `p/python` - Python-specific issues
- `p/docker` - Dockerfile best practices
- `p/ci` - CI/CD security checks

**Findings:** No critical vulnerabilities detected in current codebase.

**Strategy:** Semgrep runs as a separate job in parallel with tests. Fails the build on high/critical findings.

## Key Decisions

**Versioning Strategy:**
CalVer (`YYYY.MM.DD`) chosen because this is a continuously deployed service, not a library. Time-based versions are clearer for ops teams to understand deployment history. Tags include full date, month-only for rollups, and commit SHA for traceability.

**Docker Tags:**
- `2026.02` - Monthly rolling tag
- `2026.02.09` - Daily version
- `latest` - Latest stable (main branch only)
- `2026.02.09-<sha>` - Traceable to specific commit

**Workflow Triggers:**
Push to main/master/lab03 and PRs to main/master. Path filters prevent unnecessary runs when only docs or other apps change. This is essential in a monorepo.

**Test Coverage:**
- 97%+ coverage achieved
- All endpoints tested with multiple scenarios
- Helper functions tested independently
- Error cases validated (404, 405)
- **Not tested:** Exception handlers' error logging (requires mocking), main entry point
- **Coverage threshold:** 80% minimum enforced in pytest.ini

## Challenges

- **Initial Semgrep setup:** Required creating Semgrep account and adding token to GitHub secrets
- **Coverage configuration:** Needed to adjust paths since tests run from app_python directory
- **Docker multi-platform:** Added explicit platform list for consistency across architectures
