## Lab 7 — Loki Stack Monitoring

### Architecture
- **Components**: Loki (storage), Promtail (log collector), Grafana (visualization), `app-python`, `app-go`.
- **Flow**: Containers → Docker logging → Promtail (Docker SD, labels) → Loki (TSDB + filesystem) → Grafana Loki data source.

### Setup Guide
1. `cd monitoring`
2. `docker compose up -d`
3. Open Grafana at `http://localhost:3000` and add Loki data source with URL `http://loki:3100`.

### Configuration
- **Loki**: TSDB + `filesystem`, schema `v13`, `retention_period: 168h`, compactor enabled.
- **Promtail**: Docker SD via `/var/run/docker.sock`, filters on label `logging=promtail`, relabels container name to `container` and app label to `app`.

### Application Logging
- **Python app**: uses `logging` with a custom `JSONFormatter` writing JSON like `{"timestamp": "...", "level": "...", "message": "...", "method": "...", "path": "...", "status_code": ...}` to stdout.
- Logs important events: startup, each HTTP request (method, path, status, client IP), and errors/exceptions.

### Dashboard
- **Logs Table**: `{app=~"devops-.*"}`.
- **Request Rate**: `sum by (app) (rate({app=~"devops-.*"}[1m]))`.
- **Error Logs**: `{app=~"devops-.*"} | json | level="ERROR"`.
- **Log Level Distribution**: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`.

### Production Config
- **Resources**: `deploy.resources` limits/reservations set for Loki, Promtail, Grafana, and both apps.
- **Security**: for production, disable anonymous Grafana and set admin password via environment or `.env`.
- **Retention**: Loki 7-day retention via `limits_config.retention_period`.

### Testing
- Start stack: `cd monitoring && docker compose up -d`.
- Generate logs:
  - `for i in {1..20}; do curl http://localhost:8000/; done`
  - `for i in {1..20}; do curl http://localhost:8000/health; done`
- In Grafana Explore:
  - `{app="devops-python"}`
  - `{app="devops-python"} |= "ERROR"`
  - `{app="devops-python"} | json | method="GET"`

### Challenges
- Tuning Loki TSDB + filesystem paths and retention together.
- Getting Promtail Docker SD + label filtering correct so only app containers are scraped.

