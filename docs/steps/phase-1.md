# Phase 1 — DB Tier (PostgreSQL)

## Step 3 — Namespace + Secrets

**Goals:** Isolate tutorial resources; create and inspect Secrets.

**Concepts:** Namespaces, Secrets, `data` vs `stringData`, base64
(encoding ≠ encryption).

```bash
kubectl create namespace tutorial
kubectl config set-context --current --namespace=tutorial   # stop typing -n

kubectl create secret generic postgres-creds \
  --from-literal=postgres-password='SuperSecret123' \
  --from-literal=app-password='AppPass456'

kubectl get secret postgres-creds -o yaml                          # base64, not encrypted
kubectl get secret postgres-creds -o jsonpath='{.data.postgres-password}' | base64 -d
kubectl describe secret postgres-creds
```

!!! success "Verify"
    You can decode the secret — that's the point.
    [Step 18](phase-6.md#step-18-secrets-encryption-at-rest) addresses real
    encryption at rest.

---

## Step 4 — Deploy PostgreSQL via Helm (Bitnami chart)

**Goals:** Deploy a production-grade chart; understand StatefulSets and
persistence.

**Concepts:** Helm repos/charts/values, StatefulSet vs Deployment, PV/PVC,
StorageClass.

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo bitnami/postgresql --versions | head

# deploy/manifests/db/values-db.yaml configures:
#   auth.existingSecret: postgres-creds
#   auth.database: tutorial
#   primary.persistence.size: 1Gi
helm install pg bitnami/postgresql -n tutorial -f deploy/manifests/db/values-db.yaml

kubectl get statefulset,pods,pvc -n tutorial
kubectl describe pvc data-pg-postgresql-0      # where the data actually lives
helm status pg
helm get values pg -n tutorial                 # effective configuration
```

!!! success "Verify"
    `pg-postgresql-0` is Running; PVC is `Bound`. Understand why a StatefulSet
    (stable pod name, ordered startup, per-pod storage) instead of a Deployment.

---

## Step 5 — DB user & password management

**Goals:** Create a least-privilege app user; learn credential handling.

**Concepts:** exec into pods, Postgres roles/grants, superuser vs app user,
rotation.

```bash
kubectl exec -it pg-postgresql-0 -- psql -U postgres -d tutorial
```

```sql
-- inside psql:
CREATE USER app_user WITH PASSWORD 'AppPass456';
GRANT CONNECT ON DATABASE tutorial TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
CREATE TABLE progress (
  step INT PRIMARY KEY,
  done BOOLEAN DEFAULT false,
  ts TIMESTAMPTZ DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE ON progress TO app_user;
\l        -- list databases
\du       -- list users/roles
\dt       -- list tables
\q
```

**Rotation drill:**

```bash
kubectl create secret generic postgres-creds \
  --from-literal=postgres-password='NewSecret' \
  --from-literal=app-password='NewAppPass' \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart statefulset/pg-postgresql   # pods pick up new secret on restart
```

!!! success "Verify"
    Connect as `app_user` and confirm it can write `progress` but not create
    tables. Rule: **the app tier never uses superuser credentials.**

---

## Step 6 — Cluster DNS & Services

**Goals:** Understand how pods find each other.

**Concepts:** ClusterIP service types, DNS naming
`svc.namespace.svc.cluster.local`, headless services.

```bash
kubectl get svc -n tutorial                                # pg-postgresql ClusterIP
kubectl run dnsutils --image=busybox:1.36 --rm -it --restart=Never -- \
  nslookup pg-postgresql.tutorial.svc.cluster.local
kubectl get endpoints pg-postgresql                        # IPs behind the service
```

!!! success "Verify"
    DNS resolves the service name; endpoints match the postgres pod IP.
