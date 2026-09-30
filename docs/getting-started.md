# Getting started

## Prerequisites

- Rancher Desktop installed and running, Kubernetes enabled (k3s)
- `kubectl`, `helm` (v3), `nerdctl` (or `docker` if using moby runtime)
- Optional: `mkcert` ([step 4.2](steps/phase-4.md#42-tls)), `stern`
  (log tailing), `jq`

```bash
kubectl version --client
helm version
```

## Repo layout

The repo holds the **final state** of every file; the steps create the pieces
incrementally. Step 0.1 scaffolds this structure:

```text
k8s/                         # top-level dir for everything tutorial-related
├── README.md                # the master tutorial document
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
    └── loadgen.sh           # HPA load generator (step 7.2)
```

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

Much of the tutorial mutates **cluster** state — `kubectl scale`,
`helm rollback`, secret rotation — which no git structure captures. To restart a
phase cleanly, reset the cluster instead:

```bash
scripts/reset.sh                      # helm uninstall + delete ns + PVC cleanup
git checkout phase-2 -- deploy/       # or the whole tree
```

!!! note "Namespaces are for tenants, not steps"
    Namespaces isolate *tenants* in the cluster (`playground`, `tutorial`,
    `monitoring` here), not tutorial steps. If several learners share one
    cluster, give each learner a namespace — not each step.
