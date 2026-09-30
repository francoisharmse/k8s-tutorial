# Kubernetes Three-Tier Tutorial

> **Read this tutorial as a website:** <https://francoisharmse.github.io/k8s-tutorial/>

A hands-on, step-by-step tutorial project to learn Kubernetes from basics to advanced
topics, running on a local Rancher Desktop cluster (k3s).

The application being deployed **is the tutorial itself**: a three-tier app where nginx
serves the tutorial UI, a Python (FastAPI) middleware tier serves step content and
tracks progress, and PostgreSQL persists which steps you've completed. When you check
off a step in the browser, you've just proven all three tiers work end to end.

---

## Architecture

```
Browser ──► Ingress (Traefik, TLS)
              │
              ▼
        ┌───────────┐      /api/*      ┌───────────┐      5432      ┌────────────┐
        │ Web tier  │ ───────────────► │ App tier  │ ─────────────► │  DB tier   │
        │  nginx    │                  │  FastAPI  │                │ PostgreSQL │
        │ (static + │                  │ (python)  │                │ (Stateful- │
        │  proxy)   │                  │ Deployment│                │  Set + PVC)│
        └───────────┘                  └───────────┘                └────────────┘
        ClusterIP svc                  ClusterIP svc                Headless svc
```

| Tier | Image | Source | K8s workload |
|------|-------|--------|--------------|
| Web  | `nginx:1.27` (+ baked static assets) | Public registry | Deployment |
| App  | `k8s-tutorial-app` on `python:3.12-slim` | Built locally | Deployment |
| DB   | `bitnami/postgresql` | Public registry via Helm | StatefulSet |

## Assumptions

- **Rancher Desktop on macOS** — k3s under the hood, Traefik ingress controller, built-in
  network policy enforcement. On a Rancher Manager downstream cluster, only Step 1 and
  the ingress/TLS steps differ (flagged inline).
- **Runtime caveat:** Rancher Desktop defaults to `containerd`. Images built with
  `docker build` are invisible to k3s unless you switch to the `moby` engine or build
  with `nerdctl build` (Step 8).
- PostgreSQL and nginx are pulled from public registries. The Python app is built
  locally — deliberately, since "build → deploy → iterate" is a core real-world skill.

## Repo layout

The repo holds the **final state** of every file; the steps create the pieces
incrementally. Step 0 scaffolds this structure:

```
k8s/                         # top-level dir for everything tutorial-related
├── README.md                # this file — the master tutorial
├── mkdocs.yml               # MkDocs Material site config (author tooling)
├── docs/                    # published site source — mirrors the steps below
├── .github/workflows/       # GitHub Pages deploy (mkdocs gh-deploy)
├── Makefile                 # optional: build / deploy / reset entry points
├── steps/                   # per-step markdown served by the app
│   └── 01-verify-cluster.md ...
├── app/                     # FastAPI: /api/steps, /api/progress, /healthz, /readyz
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile           # FROM python:3.12-slim
├── static/                  # web tier: tutorial UI + nginx
│   ├── nginx.conf           # proxy /api → app service
│   └── Dockerfile           # FROM nginx:1.27 (static assets baked in)
├── db/
│   └── init.sql             # tutorial db, app_user, progress table
├── deploy/                  # everything kubectl/helm consume
│   ├── manifests/           # raw YAML (Phases 1–4, before Helm), grouped by tier
│   │   ├── namespace.yaml
│   │   ├── secrets.example.yaml
│   │   ├── app/             # deployment, service, configmap, pdb
│   │   ├── db/              # values-db.yaml, backup-cronjob.yaml
│   │   ├── ingress/
│   │   ├── netpol/
│   │   └── web/             # deployment, service, nginx-conf ConfigMap
│   └── charts/
│       └── k8s-tutorial/    # umbrella Helm chart (Phase 5)
│           ├── Chart.yaml   # dependency: bitnami/postgresql
│           ├── values.yaml  # + values-dev.yaml / values-prod.yaml
│           └── templates/   # web + app deployments, services, ingress, secrets
└── scripts/
    ├── reset.sh             # helm uninstall + delete ns + delete PVCs
    └── loadgen.sh           # HPA load generator (Step 23)
```

*`mkdocs.yml`, `docs/`, and `.github/workflows/` publish this tutorial as a
website — author tooling, not part of the Step 0 scaffold.*

## Git strategy — checkpoint tags, not branches

The tutorial is **sequential**, so work on a single `main` branch and mark
progress with **tags**:

```bash
git tag phase-1            # after the DB tier works
git tag phase-2            # app tier connected
git checkout phase-2       # restore file state if you get lost
```

Tags give per-phase savepoints without the maintenance pain of ~28 divergent
branches — a fix to an early step's manifest would otherwise need cherry-picking
forward through all of them. Branches still have their uses (experiments,
alternatives like `kustomize` vs `helm`), just not step progression.

Note that much of the tutorial mutates **cluster** state — `kubectl scale`,
`helm rollback`, secret rotation — which no git structure captures. To restart a
phase cleanly, reset the cluster instead:

```bash
scripts/reset.sh                      # helm uninstall + delete ns + PVC cleanup
git checkout phase-2 -- deploy/       # or the whole tree
```

Namespaces fill a different role: they isolate **tenants** in the cluster
(`playground`, `tutorial`, `monitoring` here), not steps. If several learners
share one cluster, give each learner a namespace — not each step.

---

## Prerequisites

- Rancher Desktop installed and running, Kubernetes enabled (k3s)
- `kubectl`, `helm` (v3), `nerdctl` (or `docker` if using moby runtime)
- Optional: `mkcert` (TLS step), `stern` (log tailing), `jq`

```bash
kubectl version --client
helm version
```

---

# The Steps

Work through each step in order. Every step has **Goals**, **Concepts**, **Commands**,
and a **Verify** checkpoint. The app's UI mirrors these same steps from `steps/*.md`.

---

## Phase 0 — Environment & Cluster Orientation

### Step 0 — Scaffold the repo

**Goals:** Create the directory layout; set up the git checkpoint-tag workflow.

**Concepts:** Single-branch + tags workflow, `.gitkeep` placeholders for empty
dirs, keeping secrets out of git from day one.

```bash
mkdir k8s && cd k8s
git init -b main

mkdir -p steps app static db scripts \
  deploy/manifests/{app,db,ingress,netpol,web} \
  deploy/charts

# git doesn't track empty dirs — placeholders keep the skeleton visible:
find . -type d -empty -exec touch {}/.gitkeep \;
```

Add a `.gitignore` covering your editor/OS noise plus these tutorial-specific
rules — real Secrets never get committed (reinforced in Step 18):

```gitignore
secrets.yaml            # secrets.example.yaml stays tracked
*-key.pem               # mkcert/openssl private keys (Step 15)
dump.sql                # pg_dump output (Step 25)
```

```bash
git add -A && git commit -m "Scaffold tutorial repo"
git tag step-00
```

**Verify:** `git log --oneline` shows the scaffold commit; `find . -type d`
matches the layout above. From here on, tag at each phase boundary
(`git tag phase-1`, …) — see *Git strategy* above.

---

### Step 1 — Verify cluster access

**Goals:** Confirm kubectl talks to the local cluster; understand contexts.

**Concepts:** kubeconfig, contexts, control plane vs worker nodes.

```bash
kubectl version --short                     # client + server versions
kubectl config get-contexts                 # confirm you're on rancher-desktop
kubectl config use-context rancher-desktop  # if needed
kubectl get nodes -o wide                   # nodes, IPs, container runtime
kubectl get pods -A                         # all system pods (k3s, traefik, coredns)
helm version
kubectl api-resources | head -30            # discover object types
```

**Verify:** Node shows `Ready`; `kube-system` pods `Running`.

---

### Step 2 — Imperative playground

**Goals:** Learn the core objects hands-on before declarative YAML.

**Concepts:** Pods, namespaces, describe/logs/exec, `kubectl explain`.

```bash
kubectl create namespace playground
kubectl run demo --image=nginx:1.27 -n playground
kubectl get pods -n playground -w             # watch the lifecycle (Ctrl+C to stop)
kubectl describe pod demo -n playground       # events, conditions, why it works
kubectl logs demo -n playground
kubectl exec -it demo -n playground -- /bin/sh
kubectl explain pod.spec.containers           # built-in API docs — use constantly
kubectl delete namespace playground           # cascades everything inside
```

**Verify:** You can explain the difference between `describe` (what happened) and
`logs` (what the app said).

---

## Phase 1 — DB Tier (PostgreSQL)

### Step 3 — Namespace + Secrets

**Goals:** Isolate tutorial resources; create and inspect Secrets.

**Concepts:** Namespaces, Secrets, `data` vs `stringData`, base64 (encoding ≠ encryption).

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

**Verify:** You can decode the secret — that's the point. Step 18 addresses real
encryption at rest.

---

### Step 4 — Deploy PostgreSQL via Helm (Bitnami chart)

**Goals:** Deploy a production-grade chart; understand StatefulSets and persistence.

**Concepts:** Helm repos/charts/values, StatefulSet vs Deployment, PV/PVC, StorageClass.

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

**Verify:** `pg-postgresql-0` is Running; PVC is `Bound`. Understand why a StatefulSet
(stable pod name, ordered startup, per-pod storage) instead of a Deployment.

---

### Step 5 — DB user & password management

**Goals:** Create a least-privilege app user; learn credential handling.

**Concepts:** exec into pods, Postgres roles/grants, superuser vs app user, rotation.

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

**Verify:** Connect as `app_user` and confirm it can write `progress` but not create
tables. Rule: **the app tier never uses superuser credentials.**

---

### Step 6 — Cluster DNS & Services

**Goals:** Understand how pods find each other.

**Concepts:** ClusterIP service types, DNS naming `svc.namespace.svc.cluster.local`,
headless services.

```bash
kubectl get svc -n tutorial                                # pg-postgresql ClusterIP
kubectl run dnsutils --image=busybox:1.36 --rm -it --restart=Never -- \
  nslookup pg-postgresql.tutorial.svc.cluster.local
kubectl get endpoints pg-postgresql                        # IPs behind the service
```

**Verify:** DNS resolves the service name; endpoints match the postgres pod IP.

---

## Phase 2 — App Tier (Python / FastAPI)

### Step 7 — Write the app

**Goals:** Build `app/main.py` — the middleware that talks to Postgres.

**Concepts:** Environment-driven config, health vs readiness semantics.

Endpoints:
- `GET /healthz` — process alive (always 200)
- `GET /readyz` — runs `SELECT 1` against Postgres; fails if DB unreachable
- `GET /api/steps` — tutorial steps
- `GET /api/progress`, `POST /api/progress` — read/write the `progress` table

Config via env: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (from Secret).

---

### Step 8 — Build the image (Rancher Desktop runtime caveat)

**Goals:** Get a locally-built image visible to k3s.

**Concepts:** Image build/push/pull lifecycle, `imagePullPolicy`, runtime namespaces.

```bash
# If Rancher Desktop uses containerd (default):
nerdctl --namespace k8s.io build -t k8s-tutorial-app:0.1.0 ./app
nerdctl --namespace k8s.io images | grep k8s-tutorial

# If using moby/dockerd instead:
docker build -t k8s-tutorial-app:0.1.0 ./app
```

**Verify:** `imagePullPolicy: IfNotPresent` + local tag → k8s uses the node-local
image. Later: `docker push` to Docker Hub/GHCR for the real registry flow.

---

### Step 9 — Deployment + ConfigMap + Secret wiring

**Goals:** Deploy the app tier declaratively; separate config from code from secrets.

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

**Verify:** `/readyz` returns DB-connected JSON through the port-forward.

---

### Step 10 — Probes & self-healing

**Goals:** Make k8s detect and route around failure.

**Concepts:** readiness vs liveness vs startup probes, `restartPolicy`, events.

```bash
kubectl describe pod -l tier=app | grep -A5 -i probes

# Chaos test: kill the DB, watch the app go NotReady (not crash — it can't serve)
kubectl delete pod pg-postgresql-0
kubectl get pods -w                              # app → 0/1 Ready until DB returns
kubectl get events --sort-by=.lastTimestamp      # watch the story unfold
```

**Verify:** App pod returns to `Ready` automatically once postgres is back.
Readiness removes it from Service endpoints — traffic never hits a broken pod.

---

### Step 11 — Resources & metrics

**Goals:** Right-size workloads; observe actual usage.

**Concepts:** requests vs limits, QoS classes (Guaranteed/Burstable/BestEffort),
OOMKill, metrics-server.

```bash
kubectl top nodes && kubectl top pods -n tutorial
kubectl describe pod -l tier=app | grep QoS

# Deliberately set a tiny memory limit → watch OOMKill → then fix it
kubectl get events --field-selector reason=OOMKilled
```

**Verify:** You can read `requests`/`limits` in a pod spec and predict its QoS class.

---

## Phase 3 — Web Tier (nginx)

### Step 12 — nginx deployment

**Goals:** Serve the tutorial UI; reverse-proxy API calls to the app tier.

**Concepts:** ConfigMap-mounted config, reverse proxy, multi-tier request flow.

```bash
nerdctl --namespace k8s.io build -t k8s-tutorial-web:0.1.0 ./static
kubectl apply -f deploy/manifests/web/   # deployment + service + nginx-conf ConfigMap
kubectl port-forward svc/web 8080:80
```

`static/nginx.conf` key block:
```nginx
location /api/ {
    proxy_pass http://app.tutorial.svc.cluster.local:8000;
}
```

**Verify:** Browser → `localhost:8080` — UI loads and the progress list (served by
web → app → postgres) renders. **All three tiers now live.**

---

### Step 13 — Config rollout without rebuild

**Goals:** Learn ConfigMap update semantics.

**Concepts:** Mounted ConfigMap volumes update, but apps don't hot-reload;
`rollout restart`; checksum annotations (revisited in Helm phase).

```bash
# edit static/nginx.conf, then:
kubectl apply -f deploy/manifests/web/nginx-conf.yaml
kubectl rollout restart deploy/web
kubectl rollout status deploy/web
```

**Verify:** New config active after restart; understand why restart was needed.

---

## Phase 4 — Ingress & TLS

### Step 14 — Ingress (Traefik, built into k3s)

**Goals:** Route external traffic by hostname/path instead of port-forward.

**Concepts:** Ingress resource vs ingress controller, host/path routing, `/etc/hosts`.

```bash
kubectl get pods -n kube-system | grep traefik     # the controller k3s ships

# add to /etc/hosts:   127.0.0.1  k8s-tutorial.local
kubectl apply -f deploy/manifests/ingress/         # host k8s-tutorial.local → svc/web:80
kubectl get ingress tutorial
kubectl describe ingress tutorial
```

**Verify:** `http://k8s-tutorial.local` loads the app — no port-forward.
*(Rancher Manager downstream cluster: controller may be nginx; external IP comes
from a LoadBalancer rather than localhost.)*

---

### Step 15 — TLS

**Goals:** Serve HTTPS; manage certs as cluster objects.

**Concepts:** TLS secret type, cert termination at ingress.

```bash
mkcert k8s-tutorial.local          # or: openssl req -x509 ...
kubectl create secret tls tutorial-tls \
  --cert=k8s-tutorial.local.pem --key=k8s-tutorial.local-key.pem
kubectl get secret tutorial-tls -o yaml        # note type: kubernetes.io/tls
# add tls: section to ingress.yaml, re-apply
```

**Verify:** `https://k8s-tutorial.local` with a trusted cert (mkcert) or browser
warning (self-signed openssl).

---

## Phase 5 — IaC: Helm-ify Everything

### Step 16 — Build the umbrella chart

**Goals:** Convert all hand-applied manifests into one versioned, parameterizable chart.

**Concepts:** Chart structure, chart dependencies, `values.yaml` hierarchy,
templates/`_helpers.tpl`, `helm template`/`lint`/`--dry-run`.

```bash
helm create deploy/charts/k8s-tutorial
# Chart.yaml dependency:
#   - name: postgresql, version: ~15.x, repository: bitnami, alias: db,
#     condition: db.enabled
helm dependency update deploy/charts/k8s-tutorial
helm lint deploy/charts/k8s-tutorial
helm template tutorial deploy/charts/k8s-tutorial | less   # render without installing
helm install tutorial deploy/charts/k8s-tutorial --dry-run --debug -n tutorial
```

Move all manifests from `deploy/manifests/` into `templates/`, parameterizing image tags, DB
settings, ingress host, and resources through `values.yaml`. Add `values-dev.yaml` /
`values-prod.yaml` to model environment promotion. Add a checksum annotation on the
web Deployment so ConfigMap changes auto-roll pods:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/web-configmap.yaml") . | sha256sum }}
```

**Verify:** `helm template` output equals what you applied by hand.

---

### Step 17 — Migrate to Helm-managed; release lifecycle

**Goals:** Own the stack as a Helm release; learn upgrade/rollback.

**Concepts:** Releases, release history secrets, `--set` vs `-f`, rollback semantics.

```bash
kubectl delete deploy/app deploy/web          # remove hand-applied versions
helm install tutorial deploy/charts/k8s-tutorial -n tutorial
helm list -n tutorial
helm get manifest tutorial                    # what Helm actually applied

helm upgrade tutorial deploy/charts/k8s-tutorial --set app.image.tag=0.2.0
helm history tutorial
helm rollback tutorial 1                      # back to revision 1
kubectl get secret -l owner=helm -n tutorial  # sh.helm.release.* — Helm's state
```

**Verify:** `helm history` shows the upgrade and rollback revisions.

---

## Phase 6 — Security

### Step 18 — Secrets encryption at rest

**Goals:** Understand why base64 Secrets aren't secure; enable etcd encryption.

**Concepts:** Secrets = base64 in etcd, EncryptionConfiguration (aescbc/KMS),
k3s `--secrets-encryption`, secret management strategy (SOPS, External Secrets).

```bash
kubectl get secret postgres-creds -o yaml     # readable → demonstrate the problem

# k3s / Rancher Desktop: enable via Preferences → Kubernetes, or k3s config:
#   /etc/rancher/k3s/config.yaml → secrets-encryption: true
# Full cluster: EncryptionConfiguration with aescbc provider.
# Verify encryption in etcd (control-plane host):
#   etcdctl get /registry/secrets/tutorial/postgres-creds | hexdump -C  → ciphertext
```

**Also cover:** why Secrets still shouldn't be committed to git → `helm-secrets`/SOPS,
or External Secrets Operator for production.

**Verify:** Secret reads fine via API, but is ciphertext in etcd.

---

### Step 19 — RBAC

**Goals:** Give workloads and humans exactly the access they need — no more.

**Concepts:** ServiceAccounts, Role vs ClusterRole, RoleBinding/ClusterRoleBinding,
`kubectl auth can-i`, automounted tokens.

```bash
kubectl create serviceaccount app-sa -n tutorial
kubectl create role app-reader --verb=get,list --resource=configmaps -n tutorial
kubectl create rolebinding app-rb --role=app-reader \
  --serviceaccount=tutorial:app-sa -n tutorial

kubectl auth can-i get configmaps --as=system:serviceaccount:tutorial:app-sa    # yes
kubectl auth can-i create secrets --as=system:serviceaccount:tutorial:app-sa    # no
kubectl auth can-i --list --as=system:serviceaccount:tutorial:app-sa            # everything it can do

# wire the SA into the app deployment:  serviceAccountName: app-sa
# inspect the mounted token inside the pod:
kubectl exec -it deploy/app -- ls /var/run/secrets/kubernetes.io/serviceaccount
kubectl exec -it deploy/app -- cat /var/run/secrets/kubernetes.io/serviceaccount/token | cut -d. -f2 | base64 -d
```

Bonus: create a `viewer` SA with `get,list,watch` on everything in `tutorial` —
a read-only "junior SRE" account.

**Verify:** `auth can-i` confirms allow/deny exactly as intended.

---

### Step 20 — Pod security & securityContext

**Goals:** Harden containers; enforce standards at the namespace level.

**Concepts:** Pod Security Standards (privileged/baseline/restricted), Pod Security
Admission labels, `securityContext` fields.

```bash
kubectl label namespace tutorial pod-security.kubernetes.io/enforce=baseline

# then harden each container:
#   securityContext:
#     runAsNonRoot: true
#     readOnlyRootFilesystem: true
#     allowPrivilegeEscalation: false
#     capabilities: { drop: [ALL] }

# try enforce=restricted before hardening → watch pods get REJECTED:
kubectl get events --field-selector reason=FailedCreate
kubectl apply -f ...   # admission error is explicit about which field violates
```

**Verify:** With `restricted` enforcement, hardened pods run and unhardened ones are
rejected with clear admission errors.

---

### Step 21 — NetworkPolicies

**Goals:** Enforce tier-to-tier traffic rules at the network level.

**Concepts:** default-deny + explicit allow, pod selectors, ingress/egress rules.
(k3s's built-in controller enforces these; not all CNIs do.)

```yaml
# deploy/manifests/netpol/: default-deny-ingress for the namespace, then allow:
#   ingress-controller → web:80
#   web → app:8000
#   app → pg-postgresql:5432
#   (+ egress to kube-dns or nothing resolves)
```

```bash
kubectl apply -f deploy/manifests/netpol/
kubectl get networkpolicy
# Test the matrix:
kubectl exec -it deploy/web -- curl -m3 http://app:8000/healthz    # allowed
kubectl exec -it deploy/app -- curl -m3 http://web:80              # denied (times out)
kubectl exec -it deploy/web -- curl -m3 pg-postgresql:5432         # denied
```

**Verify:** Exactly the allowed paths work; everything else times out. Sketch the
resulting flow: ingress → web → app → db, nothing else.

---

## Phase 7 — Operations at Scale

### Step 22 — Scaling, rolling updates, rollbacks, PDBs

**Goals:** Change running workloads safely; protect availability during disruption.

**Concepts:** replicas, rolling update (`maxSurge`/`maxUnavailable`), rollout
history, PodDisruptionBudget, cordon/drain.

```bash
kubectl scale deploy/app --replicas=3
kubectl set image deploy/app app=k8s-tutorial-app:0.2.0   # or: helm upgrade --set
kubectl rollout status deploy/app
kubectl rollout history deploy/app
kubectl rollout undo deploy/app                          # instant rollback

kubectl apply -f deploy/manifests/app/pdb.yaml           # minAvailable: 1
kubectl cordon <node>
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
kubectl uncordon <node>
```

**Verify:** During the rolling update, `kubectl get pods -w` shows old pods
terminating only after new ones are Ready — zero downtime.

---

### Step 23 — Horizontal Pod Autoscaler

**Goals:** Scale on real load.

**Concepts:** HPA, metrics-server dependency, scale-up/down stabilization windows.

```bash
kubectl autoscale deploy/app --min=2 --max=6 --cpu-percent=70
kubectl get hpa -w

# generate load:
kubectl run loadgen --image=busybox:1.36 --rm -it --restart=Never -- \
  /bin/sh -c 'while true; do wget -q -O- http://app:8000/api/steps > /dev/null; done'
# watch replicas climb → Ctrl+C → watch scale-down after cooldown
```

**Verify:** HPA scales app under load and scales back down. Requires resource
`requests` — HPA percentages are relative to them.

---

### Step 24 — Logging & debugging toolkit

**Goals:** Build the real-world debugging muscle.

**Concepts:** Log sources/rotation, events vs logs, ephemeral debug containers,
multi-pod tailing.

```bash
kubectl logs deploy/app -f --tail=50 --since=10m
kubectl logs -l tier=app --all-containers --prefix
stern app -n tutorial                                  # multi-pod tail (brew install stern)
kubectl get events -n tutorial --sort-by=.lastTimestamp -w

kubectl debug -it <pod> --image=busybox:1.36 --target=app    # ephemeral container
kubectl run netshoot --rm -it --image=nicolaka/netshoot      # the swiss army knife
```

**Verify:** Given a broken pod, you can triage: `describe` → `logs --previous` →
`debug`/`netshoot`.

---

### Step 25 — Jobs & database backup/restore

**Goals:** Run one-off and scheduled work; prove backups actually restore.

**Concepts:** Job vs CronJob, completions/backoff, `pg_dump`, backup PVC, initContainers.

```bash
# CronJob: nightly pg_dump → dedicated PVC
kubectl apply -f deploy/manifests/db/backup-cronjob.yaml
kubectl get cronjob

# trigger a manual run without waiting for the schedule:
kubectl create job manual-backup-1 --from=cronjob/db-backup
kubectl logs job/manual-backup-1

# restore drill: load the dump into a scratch database — a backup
# you've never restored is just a hope, not a backup
kubectl exec -it pg-postgresql-0 -- psql -U postgres -c 'CREATE DATABASE restore_test'
kubectl exec -i pg-postgresql-0 -- psql -U postgres -d restore_test < dump.sql
```

**Verify:** `restore_test` contains the `progress` table and its rows.

---

## Phase 8 — Advanced / Optional

### Step 26 — Observability stack (Prometheus + Grafana)

**Goals:** Metrics-based insight into the whole cluster.

**Concepts:** kube-prometheus-stack, ServiceMonitor, scrape targets, dashboards.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install mon prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
kubectl port-forward svc/mon-grafana -n monitoring 3000:80   # admin / prom-operator
```

Add a `/metrics` endpoint (prometheus-client) to the FastAPI app + a ServiceMonitor
→ app metrics appear in Grafana alongside cluster metrics.

**Verify:** Grafana dashboards show pod CPU/mem; app request metrics visible.

---

### Step 27 — GitOps preview

**Goals:** See how Helm + git replaces manual `kubectl apply` in production.

**Concepts:** Declarative desired state, drift reconciliation, Fleet/ArgoCD.

Point **Rancher Fleet** (bundled with Rancher) or ArgoCD at this repo — upgrades
become `git push`. Rancher Desktop alone doesn't include the Fleet UI; this step is
conceptual + optional install.

---

### Step 28 — Teardown & troubleshooting playbook

**Goals:** Clean removal; a repeatable triage flow.

```bash
helm uninstall tutorial -n tutorial
kubectl get pvc -n tutorial                 # PVCs survive uninstall — delete explicitly
kubectl delete namespace tutorial
```

**Troubleshooting playbook:**

| Symptom | First commands |
|---------|----------------|
| Pod `Pending` | `kubectl describe pod` → look at Events (unschedulable? PVC? image?) |
| `ImagePullBackOff` | `kubectl describe pod` → wrong tag/registry? runtime namespace? |
| `CrashLoopBackOff` | `kubectl logs --previous`, check env/config/secrets |
| App unreachable | `kubectl get endpoints <svc>` — empty means selector/probe problem |
| 502 via ingress | `kubectl get ingress`, check backend service name/port |
| DNS fails | `kubectl exec` → `nslookup`; check NetworkPolicy egress to kube-dns |

---

## Appendix — Command cheat sheet

```bash
# Orientation
kubectl get <resource> -o wide|yaml|json
kubectl explain <resource>.<field>
kubectl api-resources | grep <x>

# Lifecycle
kubectl apply -f <file|dir>
kubectl delete -f <file>
kubectl rollout status|history|undo|restart deploy/<name>

# Debugging
kubectl describe pod <p>
kubectl logs <p> [-c container] [--previous] [-f]
kubectl exec -it <p> -- <cmd>
kubectl port-forward svc/<s> <local>:<remote>
kubectl debug -it <p> --image=<img> --target=<container>

# Auth & security
kubectl auth can-i <verb> <resource> --as=<identity>
kubectl create secret generic|tls ...
kubectl create serviceaccount|role|rolebinding ...

# Helm
helm install|upgrade|rollback|uninstall <release> <chart>
helm template|lint|status|history|get values|get manifest
helm dependency update
helm repo add|update|search
```

## Appendix — Key concepts map

| Area | Objects | Steps |
|------|---------|-------|
| Workloads | Pod, Deployment, ReplicaSet, StatefulSet, Job, CronJob | 2, 4, 22, 25 |
| Config | ConfigMap, Secret, env, volumes | 3, 9, 13 |
| Networking | Service, Endpoints, DNS, Ingress, NetworkPolicy | 6, 14, 21 |
| Storage | PV, PVC, StorageClass | 4, 25 |
| Security | RBAC, SA, RoleBinding, Pod Security, TLS, encryption | 15, 18–20 |
| Ops | Probes, resources, HPA, PDB, rollouts, events | 10–11, 22–24 |
| IaC | Helm charts, releases, values, dependencies | 4, 16–17, 26 |
