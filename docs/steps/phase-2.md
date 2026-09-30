# Phase 2 — App Tier (Python / FastAPI)

## 2.1 — Write the app

**Goals:** Build `app/main.py` — the middleware that talks to Postgres.

**Concepts:** Environment-driven config, health vs readiness semantics.

Endpoints:

- `GET /healthz` — process alive (always 200)
- `GET /readyz` — runs `SELECT 1` against Postgres; fails if DB unreachable
- `GET /api/steps` — tutorial steps
- `GET /api/progress`, `POST /api/progress` — read/write the `progress` table

Config via env: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (from Secret).

---

## 2.2 — Build the image (Rancher Desktop runtime caveat)

**Goals:** Get a locally-built image visible to k3s.

**Concepts:** Image build/push/pull lifecycle, `imagePullPolicy`, runtime
namespaces.

```bash
# If Rancher Desktop uses containerd (default):
nerdctl --namespace k8s.io build -t k8s-tutorial-app:0.1.0 ./app
nerdctl --namespace k8s.io images | grep k8s-tutorial

# If using moby/dockerd instead:
docker build -t k8s-tutorial-app:0.1.0 ./app
```

!!! success "Verify"
    `imagePullPolicy: IfNotPresent` + local tag → k8s uses the node-local image.
    Later: `docker push` to Docker Hub/GHCR for the real registry flow.

---

## 2.3 — Deployment + ConfigMap + Secret wiring

**Goals:** Deploy the app tier declaratively; separate config from code from
secrets.

**Concepts:** Deployment/ReplicaSet/pod hierarchy, `envFrom`/`secretKeyRef`,
`kubectl apply`, labels/selectors.

```yaml
# deploy/manifests/app/configmap.yaml:  DB_HOST=pg-postgresql, DB_NAME=tutorial, DB_USER=app_user
# deploy/manifests/app/deployment.yaml: env secretKeyRef → postgres-creds / app-password
# deploy/manifests/app/service.yaml:    ClusterIP :8000
```

```bash
kubectl apply -f deploy/manifests/app/
kubectl rollout status deploy/app
kubectl get pods -l tier=app -o wide
kubectl logs -f deploy/app
kubectl port-forward svc/app 8000:8000 &
curl localhost:8000/readyz          # {"db":"ok"} → app↔db link proven
kubectl logs deploy/app --previous  # logs from a crashed container
```

!!! success "Verify"
    `/readyz` returns DB-connected JSON through the port-forward.

---

## 2.4 — Probes & self-healing

**Goals:** Make k8s detect and route around failure.

**Concepts:** readiness vs liveness vs startup probes, `restartPolicy`, events.

```bash
kubectl describe pod -l tier=app | grep -A5 -i probes

# Chaos test: kill the DB, watch the app go NotReady (not crash — it can't serve)
kubectl delete pod pg-postgresql-0
kubectl get pods -w                              # app → 0/1 Ready until DB returns
kubectl get events --sort-by=.lastTimestamp      # watch the story unfold
```

!!! success "Verify"
    App pod returns to `Ready` automatically once postgres is back. Readiness
    removes it from Service endpoints — traffic never hits a broken pod.

---

## 2.5 — Resources & metrics

**Goals:** Right-size workloads; observe actual usage.

**Concepts:** requests vs limits, QoS classes (Guaranteed/Burstable/BestEffort),
OOMKill, metrics-server.

```bash
kubectl top nodes && kubectl top pods -n tutorial
kubectl describe pod -l tier=app | grep QoS

# Deliberately set a tiny memory limit → watch OOMKill → then fix it
kubectl get events --field-selector reason=OOMKilled
```

!!! success "Verify"
    You can read `requests`/`limits` in a pod spec and predict its QoS class.
