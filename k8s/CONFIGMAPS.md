# Lab 12 — ConfigMaps & Persistent Volumes

## 1) Application Changes

Visits counter is implemented in `app_python/app.py`:

- `DATA_DIR` env var (default `/data`) controls where `visits` file is stored.
- `_read_visits()` / `_write_visits()` handle the file (atomic write via `os.replace`).
- `_increment_visits()` is guarded by `asyncio.Lock` so concurrent `GET /` requests don't race.
- `GET /` increments the counter and embeds the value in the response.
- `GET /visits` returns the current count without incrementing.
- `GET /config` returns the mounted ConfigMap JSON + ConfigMap-sourced env vars (verification endpoint).

Endpoints summary:

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | increments visits, returns info + current `visits` |
| GET | `/visits` | read-only view of counter |
| GET | `/config` | dump of `/config/config.json` + selected env vars |

### Local testing with Docker Compose

`app_python/docker-compose.yml` bind-mounts `./visits-data → /app/data` and sets `DATA_DIR=/app/data`.

```bash
cd app_python
mkdir -p visits-data
# container runs as non-root (uid 1000) so make the bind mount writable
sudo chown -R 1000:1000 visits-data || true
docker compose up --build -d
curl -s http://127.0.0.1:5000/ | jq '.visits'
curl -s http://127.0.0.1:5000/ | jq '.visits'
curl -s http://127.0.0.1:5000/visits
cat ./visits-data/visits
docker compose restart devops-info
curl -s http://127.0.0.1:5000/visits
```

**Evidence**

```text
…er0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/D/app_python (lab12)> curl -s http://127.0.0.1:5000/ | jq '.visits'
curl -s http://127.0.0.1:5000/ | jq '.visits'
1
2
…er0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/D/app_python (lab12)> curl -s http://127.0.0.1:5000/ | jq '.visits'
curl -s http://127.0.0.1:5000/ | jq '.visits'
3
4
…er0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/D/app_python (lab12)> curl -s http://127.0.0.1:5000/ | jq '.visits'
curl -s http://127.0.0.1:5000/ | jq '.visits'
5
6
…er0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/D/app_python (lab12)> curl -s http://127.0.0.1:5000/visits
{"visits":6,"file":"/app/data/visits"}⏎                              
…er0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/D/app_python (lab12)> docker compose restart devops-info
curl -s http://127.0.0.1:5000/visits
[+] Restarting 1/1
 ✔ Container devops-info  Started                               0.8s 
…7@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/D/app_python (lab12) [56]> curl -s http://127.0.0.1:5000/visits
{"visits":6,"file":"/app/data/visits"}⏎    
```

## 2) ConfigMap Implementation

Two ConfigMaps are rendered from one template (`templates/configmap.yaml`):

- `{{ fullname }}-config`: full `files/config.json` loaded via `.Files.Get` and mounted as a file at `/config/config.json`.
- `{{ fullname }}-env`: key/value pairs from `values.yaml` `config.env` injected as env vars via `envFrom.configMapRef`.

Relevant values (`values.yaml`):

```yaml
config:
  enabled: true
  mountPath: "/config"
  env:
    APP_ENV: "dev"
    LOG_LEVEL: "info"
    FEATURE_FLAG_BETA: "true"
    WELCOME_MESSAGE: "hello from configmap"
```

File content (`k8s/devops-info/files/config.json`):

```json
{
  "app": { "name": "devops-info-service", "version": "1.0.0" },
  "environment": "dev",
  "features": { "beta_ui": true, "verbose_logging": false, "visits_endpoint": true },
  "limits": { "max_request_bytes": 1048576, "max_visits_displayed": 1000 }
}
```

Deployment wires both:

```yaml
envFrom:
  - secretRef: { name: <fullname>-secret }
  - configMapRef: { name: <fullname>-env }
volumeMounts:
  - { name: config-volume, mountPath: /config, readOnly: true }
volumes:
  - name: config-volume
    configMap: { name: <fullname>-config }
```

### Verification

```bash
helm upgrade --install devops-info k8s/devops-info
kubectl get configmap,pvc
kubectl rollout status deploy/devops-info
POD=$(kubectl get pod -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- cat /config/config.json
kubectl exec "$POD" -- sh -c 'printenv | grep -E "APP_ENV|LOG_LEVEL|FEATURE_FLAG_BETA|WELCOME_MESSAGE"'
kubectl exec "$POD" -- wget -qO- http://localhost:5000/config
```

**Evidence**

```bash
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/DevOps-Core-Course1 (lab12)> docker compose -f k8s/docker-compose.yml exec k8s-dev bash
service "k8s-dev" is not running
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/DevOps-Core-Course1 (lab12) [1]> cd k8s
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/D/k8s (lab12)> docker compose up -d
[+] Running 1/1
 ✔ Container k8s-dev  Started                                                  0.2s 
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/D/k8s (lab12)> docker compose -f k8s/docker-compose.yml exec k8s-dev bash
open /home/woolfer0097/Code/DevOps-Core-Course1/k8s/k8s/docker-compose.yml: no such file or directory
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/D/k8s (lab12) [1]> cd ..
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/DevOps-Core-Course1 (lab12)> docker compose -f k8s/docker-compose.yml exec k8s-dev bash
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kind create cluster --name devops-lab
Creating cluster "devops-lab" ...
⢎⡱ Ensuring node image (kindest/node:v1.35.1) 🖼 ^C
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kind create cluster --name devops-lab
Creating cluster "devops-lab" ...
 ✓ Ensuring node image (kindest/node:v1.35.1) 🖼 
 ✓ Preparing nodes 📦  
 ✓ Writing configuration 📜 
 ✓ Starting control-plane 🕹️ 
 ✓ Installing CNI 🔌 
 ✓ Installing StorageClass 💾 
Set kubectl context to "kind-devops-lab"
You can now use your cluster with:

kubectl cluster-info --context kind-devops-lab

Not sure what to do next? 😅  Check out https://kind.sigs.k8s.io/docs/user/quick-start/
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kind get clusters || kind create cluster --name devops-lab
devops-lab
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl config use-context kind-devops-lab
Switched to context "kind-devops-lab".
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# helm upgrade --install devops-info k8s/devops-info
Release "devops-info" does not exist. Installing it now.
Error: repo k8s not found
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# cd ..
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm upgrade --install devops-info k8s/devops-info
Release "devops-info" does not exist. Installing it now.
NAME: devops-info
LAST DEPLOYED: Thu Apr 16 20:11:32 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
1. Get the application URL:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services devops-info)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT/

2. Check release resources:
  kubectl get all -n default -l app.kubernetes.io/instance=devops-info
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl rollout status deploy/devops-info
Waiting for deployment "devops-info" rollout to finish: 0 of 1 updated replicas are available...
deployment "devops-info" successfully rolled out
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl rollout status deploy/devops-info
deployment "devops-info" successfully rolled out
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl get configmap,pvc
NAME                           DATA   AGE
configmap/devops-info-config   1      39s
configmap/devops-info-env      4      39s
configmap/kube-root-ca.crt     1      79s

NAME                                     STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/devops-info-data   Bound    pvc-f85ed128-07ab-41f9-a2a7-1030bd63fb15   100Mi      RWO            standard       <unset>                 39s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# POD=$(kubectl get pod -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- cat /config/config.json                # paste -> section 2
kubectl exec "$POD" -- sh -c 'printenv | grep -E "APP_ENV|LOG_LEVEL|FEATURE_FLAG_BETA|WELCOME_MESSAGE"'  # paste -> section 2
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}LOG_LEVEL=info
FEATURE_FLAG_BETA=true
WELCOME_MESSAGE=hello from configmap
APP_ENV=dev
```

## 3) Persistent Volume

PVC template (`templates/pvc.yaml`) is gated by `persistence.enabled`. Values:

```yaml
persistence:
  enabled: true
  size: 100Mi
  accessMode: ReadWriteOnce
  storageClass: ""   # uses the cluster default (kind: "standard")
  mountPath: "/data"
  fsGroup: 1000      # so uid 1000 (appuser) can write to the mounted volume
```

Deployment mounts the PVC at `/data`, which is also the app's default `DATA_DIR`.
`podSecurityContext.fsGroup: 1000` ensures the mounted volume is group-owned by the appuser
so file writes from the non-root container succeed.

Access mode discussion:

- `ReadWriteOnce` — single node RW. Good for our 1-replica deployment.
- `ReadWriteMany` — would be needed if we wanted multiple replicas sharing the same PVC;
  requires a CSI driver that supports it (e.g. NFS, CephFS).
- `ReadOnlyMany` — many pods, read-only.

Because we use `ReadWriteOnce`, `replicaCount` is set to `1` in `values.yaml`
(otherwise a 2nd pod scheduled on a different node couldn't attach the volume).

### Persistence test

```bash
POD=$(kubectl get pod -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward "$POD" 5000:5000 &
for i in 1 2 3 4 5; do curl -s http://127.0.0.1:5000/ > /dev/null; done
curl -s http://127.0.0.1:5000/visits
kubectl exec "$POD" -- cat /data/visits
kill %1

kubectl delete pod "$POD"
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/instance=devops-info --timeout=120s
NEWPOD=$(kubectl get pod -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$NEWPOD" -- cat /data/visits
```

**Evidence (paste output):**

```text
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl port-forward deploy/devops-info 5000:5000 &
for i in 1 2 3 4 5; do curl -s http://127.0.0.1:5000/ > /dev/null; done
[1] 845
Unable to listen on port 5000: Listeners failed to create with the following errors: [unable to create listener: Error listen tcp4 127.0.0.1:5000: bind: address already in use unable to create listener: Error listen tcp6 [::1]:5000: bind: address already in use]
error: unable to listen on any of the requested ports: [{5000 5000}]
[1]+  Exit 1                  kubectl port-forward deploy/devops-info 5000:5000
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl port-forward deploy/devops-info 18080:5000 &
PF_PID=$!
for i in 1 2 3 4 5; do curl -s http://127.0.0.1:18080/ > /dev/null; done
[1] 865
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# Forwarding from 127.0.0.1:18080 -> 5000
Forwarding from [::1]:18080 -> 5000
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# Handling connection for 18080
^C
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# POD=$(kubectl get pod -l app.0097-Redmi-Book-Pro-15-2022:/workspace# POD=$(kubectl get pod -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')rd deploy/devops-info 18080:5000 &
kubectl port-forward deploy/devops-info 18080:5000 &
PF_PID=$!1 2 3 4 5; do curl -s http://127.0.0.1:18080/ > /dev/null; d
for i in 1 2 3 4 5; do curl -s http://127.0.0.1:18080/ > /dev/null; donel -s http://127.0.0.1:18080/visits
curl -s http://127.0.0.1:18080/visitsts   # BEFORE
kubectl exec "$POD" -- cat /data/visits   # BEFORE
kill $PF_PID
[2] 1102
Handling connection for 18080
E0416 20:18:36.546079     865 portforward.go:424] "Unhandled Error" err="an error occurred forwarding 18080 -> 5000: error forwarding port 5000 to pod 8205626d2df573432db38b0bd7a0dc789747b37ffa5eeff45e7018dc8c40711c, uid : failed to find sandbox \"8205626d2df573432db38b0bd7a0dc789747b37ffa5eeff45e7018dc8c40711c\" in store: not found"
error: lost connection to pod
[1]-  Exit 1                  kubectl port-forward deploy/devops-info 18080:5000
Forwarding from 127.0.0.1:18080 -> 5000
Forwarding from [::1]:18080 -> 5000
cat: /data/visits: No such file or directory
command terminated with exit code 1
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# jobs -l
[2]+  1102 Terminated              kubectl port-forward deploy/devops-info 18080:5000
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# jobs -l
kill %1 %2 2>/dev/null || true
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# jobs -l
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# POD=$(kubectl get pod -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
echo "$POD"
devops-info-6bf6cf5fb8-kzxcq
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl exec "$POD" -- wget -qO- http://127.0.0.1:5000/visits
error: Internal error occurred: Internal error occurred: error executing command in container: failed to exec in container: failed to start exec "cc210a154cf9eb535b284bb75ac09b77b4002ed75847b6a5ad4a0933d00eb728": OCI runtime exec failed: exec failed: unable to start container process: exec: "wget": executable file not found in $PATH
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# # show /visits
kubectl exec "$POD" -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"

# increment 5 times by calling /
kubectl exec "$POD" -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(5)]"

# evidence BEFORE
kubectl exec "$POD" -- python -c "import urllib.request; print(urllibkubectl exec "$POD" -- cat /data/visits/visits').read().decode())"
{"visits":0,"file":"/data/visits"}
{"visits":5,"file":"/data/visits"}
5rootwoolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl delete pod "$POD"
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/instance=devops-info --timeout=120s
NEWPOD=$(kubectl get pod -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$NEWPOD" -- cat /data/visits   # AFTER (should match BEFORE)
pod "devops-info-6bf6cf5fb8-kzxcq" deleted from default namespace
pod/devops-info-6bf6cf5fb8-t8hvr condition met
```

## 4) ConfigMap vs Secret

| | ConfigMap | Secret |
|---|---|---|
| Purpose | Non-sensitive configuration | Credentials, tokens, keys |
| Storage | Plaintext in etcd | Base64-encoded in etcd (encrypted at rest if configured) |
| RBAC | Same API, usually broader read access | Tighter — restrict `get`/`list` on `secrets` |
| Size limit | 1 MiB per object | 1 MiB per object |
| Injection | env / file / cmd args | env / file / cmd args |
| Typical use | feature flags, URLs, log level | DB passwords, API keys, TLS certs |

Rule of thumb: if leaking the value would not cause harm → ConfigMap, otherwise Secret.

## 5) Bonus — ConfigMap Hot Reload

### a) Default update behavior

Mounted ConfigMap files update automatically, but with delay = `kubelet syncFrequency` (default ~60s) + `configMapAndSecretChangeDetectionStrategy` cache TTL. Observed total delay is typically 30–120s.

Test:

```bash
kubectl edit configmap devops-info-config   # change a value inside config.json
# then in another shell:
watch -n1 'kubectl exec -it $(kubectl get pod -l app.kubernetes.io/instance=devops-info -o jsonpath={.items[0].metadata.name}) -- cat /config/config.json'
```

**Evidence — measured delay:**

```text
20:23:48
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:49
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:50
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:51
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:52
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:53
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:54
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:56
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:57
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:58
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:59
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:00
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:01
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:02
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:03
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:05
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:06
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:07
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:08
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:09
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:10
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:11
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:12
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:13
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:15
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:16
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:17
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:18
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:19
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:20
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:21
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:22
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
```
in another shell i edited:
```bash
20:23:48
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:49
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:50
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:51
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:52
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:53
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:54
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:56
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:57
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:58
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:23:59
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:00
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:01
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:02
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:03
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:05
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:06
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:07
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:08
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:09
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:10
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:11
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:12
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:13
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:15
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:16
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:17
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:18
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:19
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:20
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:21
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
20:24:22
{
  "app": {
    "name": "devops-info-service",
    "version": "1.0.1"
      
  },
  "environment": "dev",
  "features": {
    "beta_ui": true,
    "verbose_logging": false,
    "visits_endpoint": true
  },
  "limits": {
    "max_request_bytes": 1048576,
    "max_visits_displayed": 1000
  }
}-----
```
### b) `subPath` limitation

When a ConfigMap volume is mounted with `subPath`, Kubernetes copies the file once at
pod start — it is not a symlink into the configmap projection. Updates to the ConfigMap
are therefore NOT reflected. Use a directory mount (no `subPath`) when you need auto-updates.
We mount the whole `/config` directory without `subPath`, so auto-updates work.

### c) Implemented reload approach — `checksum/config` annotation

The Deployment carries:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

Whenever `files/config.json` or `values.yaml` `config.env` changes, the rendered
ConfigMap content changes → the sha256 of `configmap.yaml` changes → the pod
template annotation changes → `helm upgrade` rolls out new pods immediately,
bypassing the kubelet sync delay.

Demonstration:

```bash
# baseline
kubectl get pod -l app.kubernetes.io/instance=devops-info -o name
# change env value in values.yaml (e.g. WELCOME_MESSAGE)
sed -i 's/hello from configmap/hello from configmap v2/' k8s/devops-info/values.yaml
helm upgrade devops-info k8s/devops-info
# observe rollout
kubectl rollout status deploy/devops-info
kubectl get pod -l app.kubernetes.io/instance=devops-info -o name
POD=$(kubectl get pod -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- printenv WELCOME_MESSAGE
```

**Evidence (paste output):**

```bash
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl get pod -l app.kubernetes.io/instance=devops-info -o name
pod/devops-info-6bf6cf5fb8-t8hvr
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# sed -i 's/hello from configmap/hello from configmap v2/' k8s/devops-info/values.yaml
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm upgrade devops-info k8s/devops-info
Release "devops-info" has been upgraded. Happy Helming!
NAME: devops-info
LAST DEPLOYED: Thu Apr 16 20:25:28 2026
NAMESPACE: default
STATUS: deployed
REVISION: 3
TEST SUITE: None
NOTES:
1. Get the application URL:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services devops-info)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT/

2. Check release resources:
  kubectl get all -n default -l app.kubernetes.io/instance=devops-info
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl rollout status deploy/devops-info
deployment "devops-info" successfully rolled out
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl get pod -l app.kubernetes.io/instance=devops-info -o name
pod/devops-info-784c98c697-92tb8
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# POD=$(kubectl get pod -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl exec "$POD" -- printenv WELCOME_MESSAGE
hello from configmap v2
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# 
```
