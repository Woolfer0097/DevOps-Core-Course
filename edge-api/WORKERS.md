# Lab 17 — Workers deployment summary

## Deployment

| Item | Value |
|------|--------|
| **Worker URL** | `https://edge-api.devops-lab17.workers.dev` |
| **Account workers.dev subdomain** | `devops-lab17.workers.dev` (registered via dashboard/API) |
| **Worker name** | `edge-api` |
| **KV namespace** | `SETTINGS` → binding `SETTINGS` (id in `wrangler.jsonc`) |

### Routes

| Path | Purpose |
|------|--------|
| `GET /` | App info and route list |
| `GET /health` | Liveness JSON |
| `GET /edge` | Cloudflare request metadata (`request.cf`) |
| `GET /deploy` | Deployment-oriented JSON (uses plaintext `vars` + masked secret-derived contact) |
| `GET /counter` | Increment persisted visit counter in KV (`visits`) |
| `POST /counter?reset=1` | Reset counter (requires `Authorization: Bearer <API_TOKEN>` secret) |

### Configuration

- **Plaintext vars** (`wrangler.jsonc` → `vars`): `APP_NAME`, `COURSE_NAME`, `DEPLOYMENT_LABEL`. These are visible in the dashboard and in the uploaded bundle metadata; they must not hold credentials (anyone with config access can read them).
- **Secrets** (Wrangler, not in Git): `API_TOKEN`, `ADMIN_EMAIL` — used in code for auth and masked display on `/deploy`.
- **KV**: `SETTINGS` stores key `visits` for `/counter`.

### Persistence check

1. Call `GET /counter` several times and note `visits`.
2. Run `npx wrangler deploy` again (or change only `DEPLOYMENT_LABEL` and redeploy).
3. Call `GET /counter` again: the counter continues from the stored value (KV is not tied to a single Worker version). Rollbacks also do not revert KV data.

---

## Evidence (replace with your captures)

### Dashboard

Add a screenshot of **Workers & Pages → edge-api** (overview or settings) showing the Worker name and URL.

### Example `GET /edge` JSON

Run locally (replace host if your subdomain differs):

```bash
curl -sS https://edge-api.devops-lab17.workers.dev/edge
```

Example shape (values depend on the PoP and client network):

```json
{
  "colo": "FRA",
  "country": "DE",
  "city": "Frankfurt",
  "asn": 12345,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3"
}
```

This shows Cloudflare attaching **edge request metadata** on `request.cf` without your application running in a single fixed region.

### Logs / metrics

- **Logs:** `console.log` on each request (`path`, `colo`). Capture one line from `npx wrangler tail` or Workers Logs in the dashboard.
- **Metrics:** In the dashboard, open **Metrics** for the Worker and note e.g. **requests** or **errors** for the last 24 hours.

### Deployments / rollback

- Listed with: `npx wrangler deployments list`
- Rollback performed: `npx wrangler rollback 48ba41ce-150d-40f7-965e-d1bb5f14c4e9 -y -m "Lab 17 rollback demo"`, then `npx wrangler deploy` to return to the current `wrangler.jsonc` version.

---

## Global distribution (Task 3)

Workers run in Cloudflare’s **isolate runtime** close to the user: each HTTP request is handled at an edge location (a **colo**) that already received the TLS connection. You do not pick “regions” per deploy; the platform schedules execution where traffic enters. That differs from VMs or many PaaS flows where you choose regions and replicate.

**`workers.dev` vs Routes vs Custom Domains**

- **`workers.dev`**: Quick public URL `https://<worker-name>.<account-subdomain>.workers.dev` with no DNS zone on your side.
- **Routes**: Attach a Worker to URLs on a **zone already on Cloudflare** (path patterns, etc.).
- **Custom Domains**: Worker as origin for your hostname (often with managed DNS in the zone).

This lab uses **`workers.dev`** only.

---

## Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|-------------------|
| Setup complexity | Higher (cluster, networking, ingress, often GitOps) | Low (Wrangler + bindings; no servers) |
| Deployment speed | Minutes typical; image pull + roll | Seconds; lightweight bundle upload |
| Global distribution | You design multi-region / anycast / CDN | Automatic edge execution per request |
| Cost (small apps) | Cluster + nodes + load balancers add up | Generous free tier; pay per request/storage |
| State/persistence | You choose DB, volumes, operators | External bindings (KV, D1, R2, etc.), not local disk |
| Control/flexibility | Full OS, language, sidecars, CRDs | Sandboxed runtime, platform limits |
| Best use case | Long-lived services, batch, stateful systems, custom networking | HTTP APIs, auth at edge, redirects, fan-out |

### When to use which

- **Kubernetes:** Long-running containers, heavy dependencies, private networking, custom kernels, large teams operating clusters.
- **Workers:** Latency-sensitive HTTP/HTTPS logic, global APIs, JWT validation, A/B at edge, small JSON services.

**Recommendation:** Use Workers for this lab’s style of edge API; use Kubernetes when you need container-native workloads and full control over orchestration.

### Reflection

- **Easier than Kubernetes:** No nodes, images, or ingress to operate; deploy and URL in one command.
- **More constrained:** No arbitrary TCP servers, no traditional file system, CPU/memory/time limits per invocation.
- **Not Docker:** You ship a **Worker bundle**, not an OCI image; the platform supplies the runtime and scaling.
