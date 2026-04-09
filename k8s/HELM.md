# Lab 10 — Helm

## 1. Chart Overview

The Kubernetes manifests from Lab 9 were converted into a Helm chart at `k8s/devops-info`.

```text
k8s/devops-info
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── serviceaccount.yaml
    ├── NOTES.txt
    └── hooks
        ├── pre-install-job.yaml
        └── post-install-job.yaml
```

Key template files:
- `templates/deployment.yaml`: Deployment with templated image, replicas, resources, strategy, env vars, liveness/readiness probes.
- `templates/service.yaml`: Service with templated type/ports and conditional `nodePort`.
- `templates/_helpers.tpl`: shared name, fullname, selector labels, common labels.
- `templates/hooks/*.yaml`: lifecycle Jobs for pre/post install actions.

Values strategy:
- `values.yaml`: default/base values.
- `values-dev.yaml`: development overrides (single replica, smaller resources, NodePort).
- `values-prod.yaml`: production overrides (more replicas, stronger resources, LoadBalancer).

## 2. Configuration Guide

Important values:

| Key | Purpose | Default |
|---|---|---|
| `replicaCount` | Number of pods | `3` |
| `image.repository` / `image.tag` | Container image | `woolfer0097kek/devops-info-python:latest` |
| `service.type` | Service exposure model | `NodePort` |
| `service.port` / `service.targetPort` | Service and container ports | `80` / `5000` |
| `resources` | CPU/memory requests and limits | `100m/128Mi` requests, `200m/256Mi` limits |
| `probes.liveness.*` | Liveness probe settings | `/health`, port `5000` |
| `probes.readiness.*` | Readiness probe settings | `/health`, port `5000` |
| `hooks.*` | Hook behavior, image, weights, commands | Enabled |

Environment installs:

```bash
# Development
helm install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml

# Production
helm install devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml

# One-off override example
helm upgrade --install devops-info-dev k8s/devops-info \
  -f k8s/devops-info/values-dev.yaml \
  --set image.tag=latest
```

## 3. Hook Implementation

Implemented hooks:
- `pre-install` Job (`templates/hooks/pre-install-job.yaml`) with weight `-5`.
- `post-install` Job (`templates/hooks/post-install-job.yaml`) with weight `5`.

Execution order:
- Lower weight runs first, so pre-install executes before release resources.
- Post-install executes after resources are created.

Deletion policy:
- Both hooks use `helm.sh/hook-delete-policy: hook-succeeded`.
- Successful hook Jobs are removed automatically after completion.

## 4. Installation Evidence

```bash
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022 ~/C/D/k8s (lab10)> docker compose exec k8s-dev bash
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# curl -fsSL https://get.helm.sh/helm-v3.15.4-linux-amd64.tar.gz -o /tmp/helm.tgz
tar -xzf /tmp/helm.tgz -C /tmp
install -m 0755 /tmp/linux-amd64/helm /usr/local/bin/helm
helm version --short
v3.15.4+gfa9efb0
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

Have a question, bug, or feature request? Let us know! https://kind.sigs.k8s.io/#community 🙂
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:42299
CoreDNS is running at https://127.0.0.1:42299/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get nodes
NAME                       STATUS   ROLES           AGE   VERSION
devops-lab-control-plane   Ready    control-plane   31s   v1.35.1
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# cd /workspace
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm version --short
v3.15.4+gfa9efb0
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm lint k8s/devops-info
==> Linting k8s/devops-info
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm template devops-info k8s/devops-info > /tmp/devops-info-rendered.yaml
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm install --dry-run --debug devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
install.go:222: [debug] Original chart version: ""
install.go:239: [debug] CHART PATH: /workspace/k8s/devops-info

NAME: devops-info-dev
LAST DEPLOYED: Thu Apr  2 20:13:07 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
TEST SUITE: None
USER-SUPPLIED VALUES:
image:
  tag: latest
probes:
  liveness:
    initialDelaySeconds: 5
    periodSeconds: 10
  readiness:
    initialDelaySeconds: 3
    periodSeconds: 5
replicaCount: 1
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
service:
  nodePort: 30080
  type: NodePort

COMPUTED VALUES:
affinity: {}
env:
  PORT: "5000"
fullnameOverride: ""
hooks:
  deletePolicy: hook-succeeded
  enabled: true
  image: busybox:1.36
  postInstall:
    command: echo "Post-install smoke check" && sleep 5 && echo "Post-install completed"
    enabled: true
    weight: 5
  preInstall:
    command: echo "Pre-install validation" && sleep 5 && echo "Pre-install completed"
    enabled: true
    weight: -5
image:
  pullPolicy: IfNotPresent
  repository: woolfer0097kek/devops-info-python
  tag: latest
nameOverride: ""
nodeSelector: {}
podAnnotations: {}
podLabels: {}
podSecurityContext: {}
probes:
  liveness:
    failureThreshold: 3
    initialDelaySeconds: 5
    path: /health
    periodSeconds: 10
    port: 5000
    timeoutSeconds: 1
  readiness:
    failureThreshold: 2
    initialDelaySeconds: 3
    path: /health
    periodSeconds: 5
    port: 5000
    timeoutSeconds: 1
replicaCount: 1
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
securityContext: {}
service:
  nodePort: 30080
  port: 80
  targetPort: 5000
  type: NodePort
serviceAccount:
  annotations: {}
  automount: true
  create: false
  name: ""
strategy:
  maxSurge: 1
  maxUnavailable: 0
tolerations: []

HOOKS:
---
# Source: devops-info/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-dev-post-install"
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": "hook-succeeded"
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 30
  template:
    metadata:
      name: "devops-info-dev-post-install"
      labels:
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info-dev
    spec:
      restartPolicy: Never
      containers:
        - name: post-install
          image: busybox:1.36
          command:
            - /bin/sh
            - -c
            - "echo \"Post-install smoke check\" && sleep 5 && echo \"Post-install completed\""
---
# Source: devops-info/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-dev-pre-install"
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": "hook-succeeded"
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 30
  template:
    metadata:
      name: "devops-info-dev-pre-install"
      labels:
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info-dev
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install
          image: busybox:1.36
          command:
            - /bin/sh
            - -c
            - "echo \"Pre-install validation\" && sleep 5 && echo \"Pre-install completed\""
MANIFEST:
---
# Source: devops-info/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-dev
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30080
  selector:
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
---
# Source: devops-info/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-info-dev
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info
      app.kubernetes.io/instance: devops-info-dev
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info-dev
    spec:
      serviceAccountName: default
      containers:
        - name: devops-info
          image: "woolfer0097kek/devops-info-python:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 5000
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 1
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 3
            periodSeconds: 5
            timeoutSeconds: 1
            failureThreshold: 2
          env:
            - name: PORT
              value: "5000"
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
            requests:
              cpu: 50m
              memory: 64Mi

NOTES:
1. Get the application URL:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services devops-info-dev)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT/

2. Check release resources:
  kubectl get all -n default -l app.kubernetes.io/instance=devops-info-dev
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
NAME: devops-info-dev
LAST DEPLOYED: Thu Apr  2 20:13:16 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
1. Get the application URL:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services devops-info-dev)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT/

2. Check release resources:
  kubectl get all -n default -l app.kubernetes.io/instance=devops-info-dev
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm list
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                   APP VERSION
devops-info-dev default         1               2026-04-02 20:13:16.75146119 +0000 UTC  deployed        devops-info-0.1.0       1.0.0      
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl get all -l app.kubernetes.io/instance=devops-info-dev
NAME                                   READY   STATUS    RESTARTS   AGE
pod/devops-info-dev-7647678bf8-5cw5v   0/1     Running   0          22s

NAME                      TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-dev   NodePort   10.96.141.49   <none>        80:30080/TCP   22s

NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-dev   0/1     1            0           22s

NAME                                         DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-dev-7647678bf8   1         1         0       22s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl get jobs
No resources found in default namespace.
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl describe job devops-info-dev-devops-info-pre-install
Error from server (NotFound): jobs.batch "devops-info-dev-devops-info-pre-install" not found
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm get hooks devops-info-dev
---
# Source: devops-info/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-dev-post-install"
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": "hook-succeeded"
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 30
  template:
    metadata:
      name: "devops-info-dev-post-install"
      labels:
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info-dev
    spec:
      restartPolicy: Never
      containers:
        - name: post-install
          image: busybox:1.36
          command:
            - /bin/sh
            - -c
            - "echo \"Post-install smoke check\" && sleep 5 && echo \"Post-install completed\""
---
# Source: devops-info/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-dev-pre-install"
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": "hook-succeeded"
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 30
  template:
    metadata:
      name: "devops-info-dev-pre-install"
      labels:
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info-dev
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install
          image: busybox:1.36
          command:
            - /bin/sh
            - -c
            - "echo \"Pre-install validation\" && sleep 5 && echo \"Pre-install completed\""
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm status devops-info-dev
NAME: devops-info-dev
LAST DEPLOYED: Thu Apr  2 20:13:16 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
1. Get the application URL:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services devops-info-dev)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT/

2. Check release resources:
  kubectl get all -n default -l app.kubernetes.io/instance=devops-info-dev
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl get events --sort-by=.lastTimestamp | grep devops-info-dev

3m39s       Normal    SuccessfulCreate          job/devops-info-dev-pre-install          Created pod: devops-info-dev-pre-install-7j2tb
3m39s       Normal    Scheduled                 pod/devops-info-dev-pre-install-7j2tb    Successfully assigned default/devops-info-dev-pre-install-7j2tb to devops-lab-control-plane
3m38s       Normal    Pulling                   pod/devops-info-dev-pre-install-7j2tb    Pulling image "busybox:1.36"
3m32s       Normal    Created                   pod/devops-info-dev-pre-install-7j2tb    Container created
3m32s       Normal    Started                   pod/devops-info-dev-pre-install-7j2tb    Container started
3m32s       Normal    Pulled                    pod/devops-info-dev-pre-install-7j2tb    Successfully pulled image "busybox:1.36" in 6.175s (6.175s including waiting). Image size: 2217006 bytes.
3m24s       Normal    Scheduled                 pod/devops-info-dev-7647678bf8-5cw5v     Successfully assigned default/devops-info-dev-7647678bf8-5cw5v to devops-lab-control-plane
3m24s       Normal    Completed                 job/devops-info-dev-pre-install          Job completed
3m24s       Normal    ScalingReplicaSet         deployment/devops-info-dev               Scaled up replica set devops-info-dev-7647678bf8 from 0 to 1
3m24s       Normal    SuccessfulCreate          replicaset/devops-info-dev-7647678bf8    Created pod: devops-info-dev-7647678bf8-5cw5v
3m24s       Normal    SuccessfulCreate          job/devops-info-dev-post-install         Created pod: devops-info-dev-post-install-rws79
3m24s       Normal    Scheduled                 pod/devops-info-dev-post-install-rws79   Successfully assigned default/devops-info-dev-post-install-rws79 to devops-lab-control-plane
3m23s       Normal    Created                   pod/devops-info-dev-post-install-rws79   Container created
3m23s       Normal    Pulled                    pod/devops-info-dev-post-install-rws79   Container image "busybox:1.36" already present on machine and can be accessed by the pod
3m23s       Normal    Started                   pod/devops-info-dev-post-install-rws79   Container started
3m23s       Normal    Pulling                   pod/devops-info-dev-7647678bf8-5cw5v     Pulling image "woolfer0097kek/devops-info-python:latest"
3m15s       Normal    Completed                 job/devops-info-dev-post-install         Job completed
3m9s        Normal    Created                   pod/devops-info-dev-7647678bf8-5cw5v     Container created
3m9s        Normal    Pulled                    pod/devops-info-dev-7647678bf8-5cw5v     Successfully pulled image "woolfer0097kek/devops-info-python:latest" in 13.827s (13.827s including waiting). Image size: 57918661 bytes.
3m8s        Normal    Started                   pod/devops-info-dev-7647678bf8-5cw5v     Container started
3m2s        Warning   Unhealthy                 pod/devops-info-dev-7647678bf8-5cw5v     Readiness probe failed: Get "http://10.244.0.6:5000/health": dial tcp 10.244.0.6:5000: connect: connection refused
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# 
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# helm upgrade devops-info-dev k8s/devops-info -f k8s/devops-info/values-prod.yaml
Release "devops-info-dev" has been upgraded. Happy Helming!
NAME: devops-info-dev
LAST DEPLOYED: Thu Apr  2 20:17:51 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
TEST SUITE: None
NOTES:
1. Get the application URL:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services devops-info-dev)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT/

2. Check release resources:
  kubectl get all -n default -l app.kubernetes.io/instance=devops-info-dev
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl get deploy,svc -l app.kubernetes.io/instance=devops-info-dev
NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-dev   1/5     1            1           4m31s

NAME                      TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-dev   LoadBalancer   10.96.141.49   <pending>     80:30080/TCP   4m31s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace# kubectl get deploy,svc -l app.kubernetes.io/instance=devops-info-dev
NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-dev   5/5     1            5           4m35s

NAME                      TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-dev   LoadBalancer   10.96.141.49   <pending>     80:30080/TCP   4m35s
```

## 5. Operations

Install:

```bash
helm install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
```

Upgrade:

```bash
helm upgrade devops-info-dev k8s/devops-info -f k8s/devops-info/values-prod.yaml
```

Rollback:

```bash
helm history devops-info-dev
helm rollback devops-info-dev 1
```

Uninstall:

```bash
helm uninstall devops-info-dev
```

## 6. Testing & Validation

Run and paste output.

```bash
# 6.1 Lint
helm lint k8s/devops-info
```

```text
OUTPUT:

```

```bash
# 6.2 Template rendering
helm template devops-info k8s/devops-info
```

```text
OUTPUT:

```

```bash
# 6.3 Dry run
helm install --dry-run --debug devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
```

```text
OUTPUT:

```

```bash
# 6.4 Runtime resources
kubectl get pods,svc -l app.kubernetes.io/instance=devops-info-dev
```

```text
OUTPUT:

```

```bash
# 6.5 Port-forward
kubectl port-forward svc/devops-info-dev-devops-info 8080:80
```

```text
OUTPUT:

```

```bash
# 6.6 Health endpoint
curl http://localhost:8080/health
```

```text
OUTPUT:

```
