# Lab 9 — Kubernetes

## Architecture Overview

```
Internet
   │
[NodePort :30080]
   │
[Service: devops-info-svc]  (ClusterIP + NodePort)
   │  selector: app=devops-info
   ├── [Pod] devops-info-xxx
   ├── [Pod] devops-info-yyy
   └── [Pod] devops-info-zzz
         image: woolfer0097/devops-info-python:latest
         port: 5000
         resources: 100m/128Mi → 200m/256Mi
```

3 replicas (scaled to 5 in Task 4), exposed via NodePort 30080 → container 5000.

---

## Manifest Files

| File | Description |
|------|-------------|
| `deployment.yml` | 3-replica Deployment with rolling update, liveness/readiness probes, resource limits |
| `service.yml` | NodePort Service mapping :30080 → pod :5000 |

**Key choices:**
- `replicas: 3` — minimum HA without excessive resource use
- `maxUnavailable: 0` — zero downtime during rollouts
- Resources: 100m/128Mi requests, 200m/256Mi limits — appropriate for a lightweight FastAPI app
- Probes on `/health` which already exists in the app

---

## Dev Environment

Run minikube inside Docker (uses host Docker socket):

```bash
# Build and enter the container
docker compose up -d --build
docker compose exec k8s-dev bash

# Inside the container — start minikube
minikube start --driver=docker

# Verify
kubectl cluster-info
kubectl get nodes
```

---

## Deployment Evidence

```
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:42641
CoreDNS is running at https://127.0.0.1:42641/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get nodes
NAME                     STATUS     ROLES           AGE   VERSION
minikube-control-plane   NotReady   control-plane   18s   v1.35.1
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get all
NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   77s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get pods,svc
NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   94s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get pods --watch
NAME                           READY   STATUS    RESTARTS   AGE
devops-info-577cfdc466-44kkd   1/1     Running   0          28s
devops-info-577cfdc466-74qv2   1/1     Running   0          56s
devops-info-577cfdc466-z9pzj   1/1     Running   0          37s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl rollout status deployment/devops-info
deployment "devops-info" successfully rolled out
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get svc 
NAME              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
devops-info-svc   NodePort    10.96.151.119   <none>        80:30080/TCP   5m55s
kubernetes        ClusterIP   10.96.0.1       <none>        443/TCP        8m21s
```

Host machine:
```
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022 ~> curl http://localhost:8080/health
                                                  curl http://localhost:8080/
{"status":"healthy","timestamp":"2026-03-25T13:15:26.485703+00:00","uptime_seconds":127}{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-577cfdc466-74qv2","platform":"Linux","platform_version":"Linux-6.17.0-19-generic-x86_64-with-glibc2.41","architecture":"x86_64","cpu_count":12,"python_version":"3.13.12"},"runtime":{"uptime_seconds":127,"uptime_human":"0 hours, 2 minutes","current_time":"2026-03-25T13:15:26.496010+00:00","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.14.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

```
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get pods -w
NAME                           READY   STATUS    RESTARTS   AGE
devops-info-577cfdc466-44kkd   1/1     Running   0          2m41s
devops-info-577cfdc466-74qv2   1/1     Running   0          3m9s
devops-info-577cfdc466-l5686   0/1     Running   0          8s
devops-info-577cfdc466-p6b57   0/1     Running   0          8s
devops-info-577cfdc466-z9pzj   1/1     Running   0          2m50s
devops-info-577cfdc466-p6b57   1/1     Running   0          10s
devops-info-577cfdc466-l5686   1/1     Running   0          12s
^Croot@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get pods -w
NAME                           READY   STATUS    RESTARTS   AGE
devops-info-577cfdc466-44kkd   1/1     Running   0          2m51s
devops-info-577cfdc466-74qv2   1/1     Running   0          3m19s
devops-info-577cfdc466-l5686   1/1     Running   0          18s
devops-info-577cfdc466-p6b57   1/1     Running   0          18s
devops-info-577cfdc466-z9pzj   1/1     Running   0          3m
```

### Rolling update
```bash
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl set image deployment/devops-info devops-info=woolfer0097kek/devops-info-pytho
n:2026.03.19-95b3056
deployment.apps/devops-info image updated
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get pods
NAME                           READY   STATUS              RESTARTS   AGE
devops-info-577cfdc466-44kkd   1/1     Running             0          7m22s
devops-info-577cfdc466-74qv2   1/1     Running             0          7m50s
devops-info-577cfdc466-l5686   1/1     Running             0          4m49s
devops-info-577cfdc466-p6b57   1/1     Running             0          4m49s
devops-info-577cfdc466-z9pzj   1/1     Running             0          7m31s
devops-info-7649bc79c7-dldp9   0/1     ContainerCreating   0          2s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
devops-info-577cfdc466-44kkd   1/1     Running   0          7m23s
devops-info-577cfdc466-74qv2   1/1     Running   0          7m51s
devops-info-577cfdc466-l5686   1/1     Running   0          4m50s
devops-info-577cfdc466-p6b57   1/1     Running   0          4m50s
devops-info-577cfdc466-z9pzj   1/1     Running   0          7m32s
devops-info-7649bc79c7-dldp9   0/1     Running   0          3s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
devops-info-577cfdc466-44kkd   1/1     Running   0          7m24s
devops-info-577cfdc466-74qv2   1/1     Running   0          7m52s
devops-info-577cfdc466-l5686   1/1     Running   0          4m51s
devops-info-577cfdc466-p6b57   1/1     Running   0          4m51s
devops-info-577cfdc466-z9pzj   1/1     Running   0          7m33s
devops-info-7649bc79c7-dldp9   0/1     Running   0          4s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
devops-info-577cfdc466-44kkd   1/1     Running   0          7m25s
devops-info-577cfdc466-74qv2   1/1     Running   0          7m53s
devops-info-577cfdc466-l5686   1/1     Running   0          4m52s
devops-info-577cfdc466-p6b57   1/1     Running   0          4m52s
devops-info-577cfdc466-z9pzj   1/1     Running   0          7m34s
devops-info-7649bc79c7-dldp9   0/1     Running   0          5s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl rollout status deployment/devops-info -w
Waiting for deployment "devops-info" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info" successfully rolled out
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl rollout history deployment/devops-info
deployment.apps/devops-info 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
3         <none>
4         <none>
5         <none>

root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl get all
NAME                               READY   STATUS         RESTARTS   AGE
pod/devops-info-7649bc79c7-5p8cm   1/1     Running        0          2m44s
pod/devops-info-7649bc79c7-ctrl6   1/1     Running        0          2m53s
pod/devops-info-7649bc79c7-dldp9   1/1     Running        0          3m1s
pod/devops-info-7649bc79c7-f2wwv   1/1     Running        0          2m35s
pod/devops-info-7649bc79c7-qblw8   1/1     Running        0          2m26s
pod/devops-info-778c786948-w7rsq   0/1     ErrImagePull   0          80s

NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-svc   NodePort    10.96.151.119   <none>        80:30080/TCP   14m
service/kubernetes        ClusterIP   10.96.0.1       <none>        443/TCP        17m

NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info   5/5     1            5           14m

NAME                                     DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-577cfdc466   0         0         0       10m
replicaset.apps/devops-info-69b4c45c7c   0         0         0       14m
replicaset.apps/devops-info-7649bc79c7   5         5         5       3m1s
replicaset.apps/devops-info-778c786948   1         1         0       3m56s
replicaset.apps/devops-info-7bb559d788   0         0         0       5m2s
root@woolfer0097-Redmi-Book-Pro-15-2022:/workspace/k8s# kubectl describe deployment devops-info
Name:                   devops-info
Namespace:              default
CreationTimestamp:      Wed, 25 Mar 2026 13:08:55 +0000
Labels:                 app=devops-info
Annotations:            deployment.kubernetes.io/revision: 6
Selector:               app=devops-info
Replicas:               5 desired | 1 updated | 6 total | 5 available | 1 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-info
  Containers:
   devops-info:
    Image:      woolfer0097kek/devops-info-pythom:2026.02
    Port:       5000/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:5000/health delay=10s timeout=1s period=10s #success=1 #failure=3
    Readiness:  http-get http://:5000/health delay=5s timeout=1s period=5s #success=1 #failure=2
    Environment:
      PORT:        5000
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    ReplicaSetUpdated
OldReplicaSets:  devops-info-69b4c45c7c (0/0 replicas created), devops-info-577cfdc466 (0/0 replicas created), devops-info-7bb559d788 (0/0 replicas created), devops-info-7649bc79c7 (5/5 replicas created)
NewReplicaSet:   devops-info-778c786948 (1/1 replicas created)
Events:
  Type    Reason             Age                  From                   Message
  ----    ------             ----                 ----                   -------
  Normal  ScalingReplicaSet  15m                  deployment-controller  Scaled up replica set devops-info-69b4c45c7c from 0 to 3
  Normal  ScalingReplicaSet  10m                  deployment-controller  Scaled up replica set devops-info-577cfdc466 from 0 to 1
  Normal  ScalingReplicaSet  10m                  deployment-controller  Scaled down replica set devops-info-69b4c45c7c from 3 to 2
  Normal  ScalingReplicaSet  10m                  deployment-controller  Scaled up replica set devops-info-577cfdc466 from 1 to 2
  Normal  ScalingReplicaSet  10m                  deployment-controller  Scaled down replica set devops-info-69b4c45c7c from 2 to 1
  Normal  ScalingReplicaSet  10m                  deployment-controller  Scaled up replica set devops-info-577cfdc466 from 2 to 3
  Normal  ScalingReplicaSet  10m                  deployment-controller  Scaled down replica set devops-info-69b4c45c7c from 1 to 0
  Normal  ScalingReplicaSet  7m56s                deployment-controller  Scaled up replica set devops-info-577cfdc466 from 3 to 5
  Normal  ScalingReplicaSet  5m10s                deployment-controller  Scaled up replica set devops-info-7bb559d788 from 0 to 1
  Normal  ScalingReplicaSet  88s (x14 over 4m4s)  deployment-controller  (combined from similar events): Scaled up replica set devops-info-778c786948 from 0 to 1
```

## Production Considerations

**Health checks:** Liveness restarts crashed containers; readiness removes unready pods from service load balancing. `/health` returns uptime + status — sufficient to detect unhealthy state.

**Resource limits:** Prevent a single pod from starving the node. Requests allow the scheduler to place pods correctly.

**Improvements for production:**
- Use specific image tag (not `latest`) to ensure reproducible deployments
- Add `PodDisruptionBudget` to guarantee availability during node maintenance
- Use `HorizontalPodAutoscaler` instead of static replicas
- Store secrets in Kubernetes Secrets / Vault, not env vars
- Add NetworkPolicy to restrict pod-to-pod traffic

**Monitoring:** App already exposes `/metrics` (Prometheus). In production: deploy kube-state-metrics + node-exporter + Grafana stack.

---

## Challenges & Solutions

- used wrong image name and tag

---

## Bonus — Ingress with TLS

```bash
# Enable ingress addon
minikube addons enable ingress

# Generate TLS cert
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"

kubectl create secret tls tls-secret --key tls.key --cert tls.crt
kubectl apply -f ingress.yml
```
