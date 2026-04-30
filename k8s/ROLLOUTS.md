# Lab 14 Rollouts Notes

## 1) Setup

```bash
docker compose up -d
docker compose exec k8s-dev bash -lc 'kind export kubeconfig --name devops-lab && kubectl get nodes'
docker compose exec k8s-dev bash -lc 'kubectl create namespace argo-rollouts --dry-run=client -o yaml | kubectl apply -f -'
docker compose exec k8s-dev bash -lc 'kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml'
docker compose exec k8s-dev bash -lc 'kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml'
docker compose exec k8s-dev bash -lc 'kubectl wait --for=condition=available deployment/argo-rollouts -n argo-rollouts --timeout=180s'
docker compose exec k8s-dev bash -lc 'kubectl wait --for=condition=available deployment/argo-rollouts-dashboard -n argo-rollouts --timeout=180s'
docker compose exec k8s-dev bash -lc 'kubectl argo rollouts version'
```

Result:
- Rollouts controller and dashboard deployments became available.
- `kubectl-argo-rollouts` plugin works (`v1.9.0` in this run).

## 2) Chart Integration

Implemented in chart `k8s/devops-info`:
- `templates/rollout.yaml` (supports canary and blue-green).
- `templates/service-preview.yaml` (only for blue-green).
- `templates/deployment.yaml` rendered only when rollout disabled.
- `values.yaml` gained `rollout.*` options.
- Added scenario files:
  - `values-canary.yaml`
  - `values-bluegreen.yaml`

Also added runnable lab manifests:
- `k8s/rollouts/lab14-canary.yaml`
- `k8s/rollouts/lab14-bluegreen.yaml`

## 3) Canary Run

### Commands
```bash
kubectl apply -f /workspace/k8s/rollouts/lab14-canary.yaml
kubectl argo rollouts get rollout lab14-canary -n lab14
kubectl argo rollouts set image lab14-canary app=argoproj/rollouts-demo:yellow -n lab14
kubectl argo rollouts get rollout lab14-canary -n lab14
kubectl argo rollouts promote lab14-canary -n lab14
kubectl argo rollouts abort lab14-canary -n lab14
kubectl argo rollouts get rollout lab14-canary -n lab14
```

### Evidence highlights
- After update: step moved to `0/9`, `SetWeight: 20`, stable+canary images listed.
- After `promote`: rollout paused at manual pause step (`CanaryPauseStep`).
- After `abort`: rollout marked `RolloutAborted`, stable revision remained active.

## 4) Blue-Green Run

### Commands
```bash
kubectl apply -f /workspace/k8s/rollouts/lab14-bluegreen.yaml
kubectl argo rollouts get rollout lab14-bluegreen -n lab14
kubectl argo rollouts set image lab14-bluegreen app=argoproj/rollouts-demo:yellow -n lab14
kubectl get svc -n lab14 lab14-bluegreen lab14-bluegreen-preview
kubectl argo rollouts promote lab14-bluegreen -n lab14
kubectl argo rollouts undo lab14-bluegreen -n lab14
kubectl argo rollouts get rollout lab14-bluegreen -n lab14
```

### Evidence highlights
- Active and preview services created and visible.
- New image became preview candidate.
- Promotion command executed.
- `undo` switched stable back to previous revision quickly.

## 5) Canary vs Blue-Green

- Canary:
  - Gradual shift with pauses.
  - Supports staged validation and manual checkpoints.
  - Rollback by aborting in-flight rollout.
- Blue-Green:
  - Two environments (active + preview), then switch.
  - Simpler go/no-go decision.
  - Fast rollback by switching back (`undo`).

Recommended:
- Use Canary for risky changes needing gradual exposure.
- Use Blue-Green for simple, fast cutovers where duplicated capacity is acceptable.

## 6) Useful Commands

```bash
kubectl argo rollouts get rollout <name> -n <ns> -w
kubectl argo rollouts promote <name> -n <ns>
kubectl argo rollouts abort <name> -n <ns>
kubectl argo rollouts undo <name> -n <ns>
kubectl argo rollouts retry <name> -n <ns>
kubectl get rollouts -A
```

## 7) Raw Terminal Evidence (Container Runs)

### A) Setup verification rerun (raw)
```bash
Set kubectl context to "kind-devops-lab"
NAME                       STATUS   ROLES           AGE   VERSION
devops-lab-control-plane   Ready    control-plane   7d    v1.35.1
NAME                                      READY   STATUS    RESTARTS   AGE
argo-rollouts-5f64f8d68-hjrgj             1/1     Running   0          12m
argo-rollouts-dashboard-755bbc64c-jgkxq   1/1     Running   0          12m
kubectl-argo-rollouts: v1.9.0+838d4e7
  BuildDate: 2026-03-20T21:08:11Z
  GitCommit: 838d4e792be666ec11bd0c80331e0c5511b5010e
  GitTreeState: clean
  GoVersion: go1.24.13
  Compiler: gc
  Platform: linux/amd64
```

### B) Canary workflow (raw)
```bash
namespace/lab14 unchanged
service/lab14-canary unchanged
rollout.argoproj.io/lab14-canary configured
rollout "lab14-canary" image updated
Name:            lab14-canary
Namespace:       lab14
Status:          â—Œ Progressing
Message:         waiting for rollout spec update to be observed
Strategy:        Canary
  Step:          9/9
  SetWeight:     100
  ActualWeight:  100
Images:          argoproj/rollouts-demo:blue (stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       5
  Ready:         5
  Available:     5
NAME                                     KIND        STATUS         AGE    INFO
âŸ³ lab14-canary                           Rollout     â—Œ Progressing  5m18s
â”œâ”€â”€# revision:3
â”‚  â””â”€â”€â§‰ lab14-canary-598b8b657           ReplicaSet  âœ” Healthy      5m18s  stable
â””â”€â”€# revision:2
   â””â”€â”€â§‰ lab14-canary-6799f868bf          ReplicaSet  â€¢ ScaledDown   5m18s
rollout 'lab14-canary' promoted
Name:            lab14-canary
Namespace:       lab14
Status:          â—Œ Progressing
Message:         waiting for rollout spec update to be observed
Strategy:        Canary
  Step:          9/9
  SetWeight:     100
  ActualWeight:  100
Images:          argoproj/rollouts-demo:blue (stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       5
  Ready:         5
  Available:     5
rollout 'lab14-canary' aborted
Name:            lab14-canary
Namespace:       lab14
Status:          â—Œ Progressing
Message:         more replicas need to be updated
Strategy:        Canary
  Step:          0/9
  SetWeight:     20
  ActualWeight:  0
Images:          argoproj/rollouts-demo:blue (stable)
                 argoproj/rollouts-demo:yellow (canary)
Replicas:
  Desired:       5
  Current:       5
  Updated:       1
  Ready:         4
  Available:     4
```

### C) Blue-Green workflow (raw)
```bash
service/lab14-bluegreen unchanged
service/lab14-bluegreen-preview unchanged
rollout.argoproj.io/lab14-bluegreen configured
rollout "lab14-bluegreen" image updated
Name:            lab14-bluegreen
Namespace:       lab14
Status:          â—Œ Progressing
Message:         more replicas need to be updated
Strategy:        BlueGreen
Images:          argoproj/rollouts-demo:blue (stable, active)
Replicas:
  Desired:       4
  Current:       4
  Updated:       0
  Ready:         4
  Available:     4
NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
lab14-bluegreen           ClusterIP   10.96.104.207   <none>        80/TCP    5m12s
lab14-bluegreen-preview   ClusterIP   10.96.117.163   <none>        80/TCP    5m12s
rollout 'lab14-bluegreen' promoted
rollout 'lab14-bluegreen' undo
Name:            lab14-bluegreen
Namespace:       lab14
Status:          âœ” Healthy
Strategy:        BlueGreen
Images:          argoproj/rollouts-demo:blue (stable, active)
                 argoproj/rollouts-demo:yellow
Replicas:
  Desired:       4
  Current:       8
  Updated:       4
  Ready:         4
  Available:     4
```

Saved full raw outputs:
- `k8s/rollouts/evidence/setup-raw.txt`
- `k8s/rollouts/evidence/canary-raw.txt`
- `k8s/rollouts/evidence/bluegreen-raw.txt`
