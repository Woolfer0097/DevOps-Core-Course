# Lab 15 — StatefulSets & Persistent Storage

## 1) StatefulSet Concepts

StatefulSet is used when pods need:
- Stable pod identity (`name-0`, `name-1`, `name-2`)
- Stable storage per pod (own PVC for each replica)
- Ordered create/update/delete behavior

Deployment vs StatefulSet:

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod identity | Ephemeral/random suffix | Stable ordinal name |
| Storage | Usually shared/one PVC pattern | Per-pod PVC via template |
| Scale/update order | Unordered | Ordered by ordinal |
| Typical workloads | Stateless APIs/web | DBs, queues, clustered systems |

Headless Service (`clusterIP: None`) is required so each pod gets resolvable DNS:
- `devops-info-0.devops-info-headless.default.svc.cluster.local`
- `devops-info-1.devops-info-headless.default.svc.cluster.local`

## 2) Implementation (Helm)

Implemented in chart `k8s/devops-info`:
- Added `templates/statefulset.yaml`
- Added `templates/service-headless.yaml`
- Kept normal service for app access
- Added persistence options used by `volumeClaimTemplates`

Used values:

```yaml
replicaCount: 3
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
  accessMode: ReadWriteOnce
  mountPath: /data
```

Deploy (dockerized k8s workflow used in this lab):

```bash
docker compose -f k8s/docker-compose.yml up -d
docker compose -f k8s/docker-compose.yml exec k8s-dev bash -lc '
  cd /workspace
  kubectl config use-context kind-devops-lab
  docker build -t devops-info-python:lab15 ./app_python
  kind load docker-image devops-info-python:lab15 --name devops-lab
  helm upgrade --install devops-info k8s/devops-info \
    -f k8s/devops-info/values-statefulset.yaml \
    --set image.repository=devops-info-python \
    --set image.tag=lab15 \
    --set image.pullPolicy=IfNotPresent
  kubectl rollout status statefulset/devops-info --timeout=240s
  kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=devops-info -o wide
'
```

Evidence:

```text
NAME                READY   STATUS    RESTARTS   AGE   IP            NODE                       NOMINATED NODE   READINESS GATES
pod/devops-info-0   1/1     Running   0          12s   10.244.0.39   devops-lab-control-plane   <none>           <none>
pod/devops-info-1   1/1     Running   0          22s   10.244.0.38   devops-lab-control-plane   <none>           <none>
pod/devops-info-2   1/1     Running   0          32s   10.244.0.37   devops-lab-control-plane   <none>           <none>

NAME                           READY   AGE     CONTAINERS    IMAGES
statefulset.apps/devops-info   3/3     2m59s   devops-info   devops-info-python:lab15

NAME                           TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE     SELECTOR
service/devops-info            ClusterIP   10.96.23.182   <none>        5000/TCP   2m59s   app.kubernetes.io/instance=devops-info,app.kubernetes.io/name=devops-info
service/devops-info-headless   ClusterIP   None           <none>        5000/TCP   2m59s   app.kubernetes.io/instance=devops-info,app.kubernetes.io/name=devops-info

NAME                                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE     VOLUMEMODE
persistentvolumeclaim/data-volume-devops-info-0   Bound    pvc-2f4ee4a9-14ab-4879-8cd6-49df8efe9c0d   100Mi      RWO            standard       <unset>                 2m59s   Filesystem
persistentvolumeclaim/data-volume-devops-info-1   Bound    pvc-f55fbb88-90b2-4415-a7f1-57ff4d3943b7   100Mi      RWO            standard       <unset>                 2m47s   Filesystem
persistentvolumeclaim/data-volume-devops-info-2   Bound    pvc-e2ce7afd-1a80-4a7d-9e68-c1c2528c16d1   100Mi      RWO            standard       <unset>                 2m35s   Filesystem
```

## 3) Network Identity (Headless DNS)

Commands:

```bash
kubectl exec devops-info-0 -- python -c "import socket; print('pod1', socket.gethostbyname('devops-info-1.devops-info-headless.default.svc.cluster.local')); print('pod2', socket.gethostbyname('devops-info-2.devops-info-headless.default.svc.cluster.local'))"
```

Evidence:

```text
pod1 10.244.0.38
pod2 10.244.0.37
```

## 4) Per-Pod Storage Isolation

Test by calling each pod locally from inside the pod:

```bash
kubectl exec devops-info-0 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(3)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
kubectl exec devops-info-1 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(5)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
kubectl exec devops-info-2 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(2)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
```

Evidence:

```text
{"visits":3,"file":"/data/visits"}
{"visits":5,"file":"/data/visits"}
{"visits":2,"file":"/data/visits"}
```

Conclusion: each pod has isolated counter data (separate PVC).

## 5) Persistence Test

Commands:

```bash
kubectl exec devops-info-0 -- cat /data/visits
kubectl delete pod devops-info-0
kubectl wait --for=condition=Ready pod/devops-info-0 --timeout=180s
kubectl exec devops-info-0 -- cat /data/visits
```

Evidence:

```text
before:
3pod "devops-info-0" deleted from default namespace
pod/devops-info-0 condition met
after:
3
```

Conclusion: data persists across pod recreation because PVC is retained and reattached.

## 6) Bonus — Update Strategies

### Partitioned rolling update

```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2
```

Result:
- Only pods with ordinal `>= 2` update first.
- Useful for canarying on highest ordinal replicas.

Evidence:

```text
Waiting for partitioned roll out to finish: 0 out of 1 new pods have been updated...
partitioned roll out complete: 1 new pods have been updated...
NAME            IMAGE                       READY
devops-info-0   devops-info-python:lab15    true
devops-info-1   devops-info-python:lab15    true
devops-info-2   devops-info-python:lab15p   true
```

### OnDelete strategy

```yaml
updateStrategy:
  type: OnDelete
```

Result:
- Pods are updated only when manually deleted.
- Useful for strict maintenance windows and controlled failover.

Evidence:

```text
after upgrade (before delete):
NAME            IMAGE                       READY
devops-info-0   devops-info-python:lab15    true
devops-info-1   devops-info-python:lab15    true
devops-info-2   devops-info-python:lab15p   true
pod "devops-info-2" deleted from default namespace
pod/devops-info-2 condition met
after manual delete:
NAME            IMAGE                        READY
devops-info-0   devops-info-python:lab15     true
devops-info-1   devops-info-python:lab15     true
devops-info-2   devops-info-python:lab15od   true
```

## 7) Useful Commands

```bash
kubectl get statefulset,pods,pvc
kubectl describe statefulset devops-info
kubectl get pod devops-info-0 -o yaml | rg claimName
kubectl delete pod devops-info-0
kubectl rollout status statefulset/devops-info
```
