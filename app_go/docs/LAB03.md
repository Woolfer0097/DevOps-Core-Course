# Lab 3 Bonus — Go CI/CD Implementation

## Overview (Multi-App CI - 1.5 pts)

**Testing Framework:** Go's built-in testing package (standard, no external dependencies)

**Endpoints Covered:**
- `GET /` - System and service information endpoint
- `GET /health` - Health check endpoint
- Error handling (404)

**Versioning Strategy:** Calendar Versioning (CalVer) - `YYYY.MM.DD` format (consistent with Python app)
- **Rationale:** Consistent versioning across all services in the monorepo

**CI Trigger Configuration:**
- Runs on push to `main`, `master`, `lab03` branches
- Runs on pull requests to `main`, `master`
- **Path filters:** Only triggers when `app_go/` files or workflow file changes
- **Independence:** Runs in parallel with Python CI, completely independent

## Workflow Evidence

**Workflow Structure:**
```
test → Runs golangci-lint and unit tests with coverage
security → Semgrep security scanning (Go-specific rules)
docker → Builds and pushes Docker images (depends on test + security)
```

**Local Testing:**
```bash
cd app_go
go test -v -cover ./...
```

**Docker Images:** `woolfer0097/devops-info-go`
- Tags: `2026.02`, `2026.02.09`, `latest`, `2026.02.09-<sha>`

**Status Badge:** See README.md

## Test Coverage (1 pt)

**Coverage Tool:** Go's built-in coverage tool (`go test -cover`)
**Integration:** Codecov.io (free for public repos)

**Current Coverage:** 76.1%
- All HTTP handlers tested
- Helper functions tested
- Error cases validated
- Benchmark tests included

**What's Covered:**
- ✅ Main endpoint handler with full response validation
- ✅ Health check endpoint
- ✅ 404 error handling
- ✅ System info collection
- ✅ Runtime info with uptime
- ✅ Request info extraction
- ✅ JSON response formatting
- ✅ Custom user agents
- ✅ Duration formatting

**What's Not Covered:**
- ❌ Main function (server startup) - requires integration test
- ❌ Some error paths in production code

**Coverage Threshold:** 70% minimum (current: 76.1%)

**Coverage Badge:** Added to README with Codecov flag `go-unittests`

## Path Filters Implementation

**Python Workflow Paths:**
```yaml
paths:
  - 'app_python/**'
  - '.github/workflows/python-ci.yml'
```

**Go Workflow Paths:**
```yaml
paths:
  - 'app_go/**'
  - '.github/workflows/go-ci.yml'
```

**Benefits of Path Filters:**
1. **CI Efficiency:** Only relevant workflows run, saving CI minutes
2. **Faster Feedback:** Developers get feedback only for code they changed
3. **Reduced Noise:** No spurious workflow runs for unrelated changes
4. **Parallel Execution:** Both workflows can run simultaneously for multi-app changes
5. **Cost Savings:** Less compute time = lower costs (important for private repos)

**Testing Path Filters:**
- Change only Python files → Only Python CI runs
- Change only Go files → Only Go CI runs
- Change both → Both CIs run in parallel
- Change only docs → No CI runs

## Best Practices Implemented

1. **Dependency Caching:** `actions/setup-go` with built-in caching
2. **Job Dependencies:** Docker build only runs if tests and security pass
3. **Path Filters:** Intelligent triggering for monorepo efficiency
4. **Multi-platform Builds:** Docker images for amd64 and arm64
5. **Docker Layer Caching:** GitHub Actions cache reduces build time
6. **Race Detector:** `go test -race` catches concurrency issues
7. **Security Scanning (Semgrep):** Go-specific security rules

### Linting with golangci-lint

**Configuration:** `.golangci.yml` with multiple linters:
- `errcheck` - Unchecked errors
- `gosimple` - Code simplification
- `govet` - Standard checks
- `staticcheck` - Static analysis
- `gosec` - Security issues
- `gofmt` - Code formatting
- `revive` - Fast linter

**Findings:** All checks pass

## Key Decisions

**Versioning Strategy:**
CalVer (`YYYY.MM.DD`) for consistency with Python app. Easier to coordinate releases across multiple services in the monorepo.

**Docker Tags:**
Same strategy as Python app for consistency:
- `2026.02` - Monthly rolling tag
- `2026.02.09` - Daily version
- `latest` - Latest stable (main branch only)
- `2026.02.09-<sha>` - Commit-specific

**Workflow Triggers:**
Identical to Python workflow for consistency, with path filters for efficiency.

**Test Coverage:**
Go's built-in coverage tool is sufficient. 76% coverage exceeds typical Go project averages (50-60%). Focus on handler and business logic testing.

## Multi-App CI Benefits

**Before Path Filters:**
- All workflows run on every commit
- Wasted CI minutes
- Slower feedback loops
- Unnecessary failures

**After Path Filters:**
- ✅ Only relevant workflows run
- ✅ ~50% reduction in CI runs for single-app changes
- ✅ Faster PR checks
- ✅ Better resource utilization

**Example Scenarios:**
1. **Python-only change:** Only Python CI runs (saves 3-5 min)
2. **Go-only change:** Only Go CI runs (saves 3-5 min)
3. **Multi-app change:** Both run in parallel (no time penalty)
4. **Doc-only change:** No CI runs (saves 6-10 min)

## Challenges

- **Go linter configuration:** Required tuning rules for project style
- **Coverage configuration:** Needed to set up Codecov flags for multi-app coverage
- **Path filter testing:** Verified filters work correctly before relying on them
