# Lab 11 — Secrets & Vault

## 1) Kubernetes Secrets

Create secret:

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=lab-user \
  --from-literal=password=lab-pass-123
```

View secret:

```bash
kubectl get secret app-credentials -o yaml
```

Decode values:

```bash
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d && echo
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d && echo
```

Notes:
- Base64 is encoding, not encryption.
- By default, Secret data in etcd is not strongly protected unless encryption at rest is enabled.
- Enable etcd encryption for production clusters and keep strict RBAC on Secret reads.

## 2) Helm Secret Integration

Chart changes:
- Added `k8s/devops-info/templates/secrets.yaml`.
- Added `secrets.*` config in `k8s/devops-info/values.yaml`.
- Deployment now loads all secret keys via `envFrom.secretRef`.

Verify:

```bash
helm upgrade --install devops-info-dev k8s/devops-info
kubectl get secret | rg devops-info
kubectl exec deploy/devops-info-dev -- printenv | rg 'username|password|APP_ENV|LOG_LEVEL'
```

Security note:
- `kubectl describe pod` does not print resolved secret values, only references.

## 3) Resource Management

Configured in `values.yaml` and used by Deployment:

```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

Explanation:
- `requests`: minimum guaranteed resources for scheduling.
- `limits`: hard cap for runtime usage.
- Start from measured baseline and tune by load tests and HPA behavior.

## 4) Vault Integration

Install (dev mode):

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
kubectl get pods
```

Configure Vault:

```bash
kubectl exec -it vault-0 -- sh
vault secrets enable -path=secret kv-v2
vault kv put secret/myapp/config db_url="postgres://demo" api_key="demo-key"
vault auth enable kubernetes
```

Policy + role (sanitized):

```hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

```bash
vault policy write devops-info-policy /tmp/devops-info-policy.hcl
vault write auth/kubernetes/role/devops-info-role \
  bound_service_account_names=devops-info-devops-info \
  bound_service_account_namespaces=default \
  policies=devops-info-policy \
  ttl=24h
```

Injection proof:

```bash
kubectl exec deploy/devops-info-dev -c devops-info -- ls /vault/secrets
kubectl exec deploy/devops-info-dev -c devops-info -- cat /vault/secrets/config
```

Sidecar pattern:
- Vault Agent injector mutates pod spec.
- Agent authenticates with Kubernetes ServiceAccount JWT.
- Agent writes secrets to files under `/vault/secrets` and refreshes renewable data.

## 5) Security Analysis

Kubernetes Secrets:
- Simple and native.
- Good for small setups with strong RBAC + etcd encryption.
- Weak for centralized secret governance and dynamic credentials.

Vault:
- Centralized policies, auditing, rotation, dynamic and leased secrets.
- Better for production and multi-environment security controls.

Recommendation:
- Use K8s Secrets only for low-risk/simple cases.
- Use Vault for production-grade secret lifecycle and access control.

## Bonus

Implemented:
- `vault.hashicorp.com/agent-inject-template-config` annotation in Deployment.
- Named template `devops-info.envVars` in `_helpers.tpl`.
- Deployment includes `{{ include "devops-info.envVars" . }}` for DRY env definitions.

Rotation behavior:
- Vault Agent renews/refreshes secret material and rewrites rendered files.
- Optional `vault.hashicorp.com/agent-inject-command` can trigger app reload after updates.

RESULT:

```bash
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# # 1) See whether kind cluster is actually running
kind get clusters
docker ps --format 'table {{.Names}}\t{{.Status}}' | rg devops-lab

# 2) If cluster exists but api is broken, recreate cleanly
kind delete cluster --name devops-lab
kind create cluster --name devops-lab

# 3) Re-check connectivity
kubectl cluster-info --context kind-devops-lab
kubectl get nodes
devops-lab
minikube
bash: rg: command not found
Deleting cluster "devops-lab" ...
Deleted nodes: ["devops-lab-control-plane"]
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
Kubernetes control plane is running at https://127.0.0.1:33053
CoreDNS is running at https://127.0.0.1:33053/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
NAME                       STATUS     ROLES           AGE   VERSION
devops-lab-control-plane   NotReady   control-plane   6s    v1.35.1
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# # 1) Check/restore cluster context
kubectl config get-contexts
kubectl config current-context

# if empty, recreate your kind cluster (or start the one you used before)
kind create cluster --name devops-lab
kubectl cluster-info --context kind-devops-lab
kubectl config use-context kind-devops-lab
CURRENT   NAME              CLUSTER           AUTHINFO          NAMESPACE
*         kind-devops-lab   kind-devops-lab   kind-devops-lab   
kind-devops-lab
ERROR: failed to create cluster: node(s) already exist for a cluster with the name "devops-lab"
Kubernetes control plane is running at https://127.0.0.1:33053
CoreDNS is running at https://127.0.0.1:33053/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
Switched to context "kind-devops-lab".
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# curl -fsSL https://get.helm.sh/helm-v3.15.4-linux-amd64.tar.gz -o /tmp/helm.tgz
tar -xzf /tmp/helm.tgz -C /tmp
install -m 0755 /tmp/linux-amd64/helm /usr/local/bin/helm
helm version --short
v3.15.4+gfa9efb0
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# apt-get update && apt-get install -y ripgrep
rg --version
Get:1 http://deb.debian.org/debian bookworm InRelease [151 kB]
Get:2 https://download.docker.com/linux/debian bookworm InRelease [46.6 kB]        
Get:3 http://deb.debian.org/debian bookworm-updates InRelease [55.4 kB]
Get:4 http://deb.debian.org/debian-security bookworm-security InRelease [48.0 kB]
Get:5 http://deb.debian.org/debian bookworm/main amd64 Packages [8792 kB]
Get:6 https://download.docker.com/linux/debian bookworm/stable amd64 Packages [66.6 kB]
Get:7 http://deb.debian.org/debian bookworm-updates/main amd64 Packages [6924 B]
Get:8 http://deb.debian.org/debian-security bookworm-security/main amd64 Packages [294 kB]
Fetched 9461 kB in 4s (2482 kB/s)                         
Reading package lists... Done
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following NEW packages will be installed:
  ripgrep
0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.
Need to get 1253 kB of archives.
After this operation, 4666 kB of additional disk space will be used.
Get:1 http://deb.debian.org/debian bookworm/main amd64 ripgrep amd64 13.0.0-4+b2 [1253 kB]
Fetched 1253 kB in 1s (950 kB/s)  
debconf: delaying package configuration, since apt-utils is not installed
Selecting previously unselected package ripgrep.
(Reading database ... 12573 files and directories currently installed.)
Preparing to unpack .../ripgrep_13.0.0-4+b2_amd64.deb ...
Unpacking ripgrep (13.0.0-4+b2) ...
Setting up ripgrep (13.0.0-4+b2) ...
ripgrep 13.0.0
-SIMD -AVX (compiled)
+SIMD +AVX (runtime)
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl create secret generic app-credentials \
  --from-literal=username=lab-user \
  --from-literal=password=lab-pass-123
secret/app-credentials created
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# 
helm lint /workspace/k8s/devops-info
helm template devops-info-dev /workspace/k8s/devops-info | rg "kind: Secret|envFrom|vault.hashicorp.com"
==> Linting /workspace/k8s/devops-info
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
kind: Secret
          envFrom:
```