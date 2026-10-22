# Kubernetes Three-Tier Tutorial

A hands-on, step-by-step tutorial project to learn Kubernetes from basics to
advanced topics, running on a local Rancher Desktop cluster (k3s).

The application being deployed **is the tutorial itself**: a three-tier app where
nginx serves the tutorial UI, a Python (FastAPI) middleware tier serves step
content and tracks progress, and PostgreSQL persists which steps you've
completed. When you check off a step in the browser, you've just proven all three
tiers work end to end.

## Solution Architecture

Solution overview — three tiers, front to back:

```mermaid
flowchart LR
    browser([Browser]) --> ingress[Ingress<br>Traefik · TLS]
    ingress --> web[Web tier<br>nginx — static + proxy<br>ClusterIP svc]
    web -->|/api/*| app[App tier<br>FastAPI Deployment<br>ClusterIP svc]
    app -->|5432| db[(DB tier<br>PostgreSQL<br>StatefulSet + PVC<br>Headless svc)]
```

## Kubernetes Architecture

Zooming into the cluster, every request flows the same chain:
**name resolution → traffic entry → Service → Pods** — where each Service
fronts a workload (Deployment or StatefulSet) that keeps its Pods alive:

```mermaid
flowchart TD
    subgraph host["Your machine"]
        browser([Browser])
    end

    subgraph cluster["Kubernetes cluster - namespace: tutorial"]
        DNS["CoreDNS<br/>svc.cluster.local"]
        ING["Ingress / LoadBalancer<br/>Traefik, TLS termination<br/>Phase 4 - until then: port-forward"]

        subgraph web_tier["Web tier - frontend"]
            SW["Service web :80<br/>ClusterIP"]
            DW["Deployment web x2<br/>nginx serves React UI"]
            PW1["pod web-1"]
            PW2["pod web-2"]
            CMW["ConfigMap nginx-conf"]
        end

        subgraph app_tier["App tier - backend"]
            SA["Service app :8000<br/>ClusterIP"]
            DA["Deployment app x2<br/>FastAPI"]
            PA1["pod app-1"]
            PA2["pod app-2"]
            CMA["ConfigMap app-config"]
            SEC["Secret postgres-creds"]
        end

        subgraph db_tier["DB tier"]
            SD["Service pg-postgresql :5432"]
            STS["StatefulSet pg-postgresql<br/>PostgreSQL"]
            PD["pod pg-postgresql-0"]
            PVC[("PVC - persistent<br/>data volume")]
        end
    end

    browser -->|"localhost:8080"| ING
    ING -->|"path /"| SW
    ING -->|"path /api"| SA
    SW -->|"selector tier=web"| DW
    DW --> PW1
    DW --> PW2
    CMW -.->|"mounted /etc/nginx/conf.d"| DW
    PW1 -->|"proxy_pass /api"| SA
    PW2 -->|"proxy_pass /api"| SA
    SA -->|"selector tier=app"| DA
    DA --> PA1
    DA --> PA2
    CMA -.->|"env DB_HOST, DB_NAME, DB_USER"| DA
    SEC -.->|"env DB_PASSWORD"| DA
    PA1 -->|"psql 5432"| SD
    PA2 -->|"psql 5432"| SD
    SD --> STS
    STS --> PD
    PD --> PVC
    DNS -.->|"resolves svc.cluster.local"| PW1
    DNS -.->|"resolves"| PA1
    DNS -.->|"resolves"| PD
```

Reading the flow:

- **DNS** — CoreDNS resolves `app.tutorial.svc.cluster.local` inside the
  cluster (step 1.4); the browser only ever talks to localhost.
- **Ingress / LoadBalancer** — the cluster's front door: one entry point that
  routes by hostname/path and terminates TLS (Phase 4). Until then,
  `port-forward` fills the role.
- **Services** — stable virtual IPs + DNS names in front of ephemeral Pods.
  `ClusterIP` = cluster-internal only; `LoadBalancer`/`NodePort` = exposed.
- **Deployments → Pods** — the workload declares desired replicas; the
  ReplicaSet keeps that many Pods running. StatefulSet + PVC does the same
  for Postgres, with stable identity and persistent storage.

| Tier | Image | Source | K8s workload |
|------|-------|--------|--------------|
| Web  | `k8s-tutorial-web` — React/Vite build on `nginx:alpine` | Built locally | Deployment |
| App  | `k8s-tutorial-app` on `python:3.12-slim` | Built locally | Deployment |
| DB   | `bitnami/postgresql` | Public registry via Helm | StatefulSet |

*Under the hood:* those pods are scheduled and kept alive by Kubernetes
itself — API server, etcd, scheduler, controller manager, and the kubelets on
each node. See [Kubernetes architecture](reference/architecture.md) for how the
control plane works and what happens when you `kubectl create`.

# Kubernetes Core components

The eight building blocks every workload is assembled from — each is exercised
hands-on at the phase noted:

| Component | What it is | Used for | In this tutorial |
|-----------|-----------|----------|------------------|
| **Pod** | Smallest deployable unit — one or more containers sharing a network namespace and storage | Where your code actually runs; ephemeral — always managed by a higher-level workload, never created bare | Every phase — `kubectl get pods` is your daily view |
| **Deployment** | Controller that keeps *N* identical Pods running via a ReplicaSet | Stateless workloads — rolling updates, rollbacks, self-healing restarts | Web and app tiers (`web`, `app`) — Phases 2–3 |
| **StatefulSet** | Like a Deployment but with stable identity: ordered names (`pg-postgresql-0`), stable DNS, per-pod storage | Stateful workloads — databases, queues, anything that can't be freely interchanged | PostgreSQL — Phase 1 |
| **Service** | Stable virtual IP + DNS name fronting a set of Pods selected by labels | Load-balancing and service discovery — Pods die and get new IPs; Services don't | `web`, `app`, `pg-postgresql` — Phase 1.4 onward |
| **Ingress** | L7 routing rules: hostname/path → Service, handled by an ingress controller | One external entry point for many Services; TLS termination; virtual hosting | Phase 4 — replaces `port-forward` |
| **ConfigMap** | Non-secret key/value config, consumable as env vars or mounted files | Decoupling config from images — change config without rebuilding | `app-config` env, `nginx-conf` file — Phases 2.4, 3.2 |
| **Secret** | Same mechanics as a ConfigMap but for sensitive values (base64, tighter access controls) | Passwords, tokens, certs — injected as env vars or files; never committed | `postgres-creds` — Phase 1.1 |
| **Volume / PVC** | Storage attachable to a Pod — `emptyDir` (ephemeral) or a `PersistentVolumeClaim` binding to real disk | Data that must outlive the Pod; a PVC survives deletes and reschedules | `pg-postgresql` data — Phase 1.2 |

See [Terminology](reference/terminology.md) for the wider vocabulary —
operators, probes, RBAC, Helm, and the managed platforms these run on.

## Assumptions

- **Rancher Desktop on macOS** — k3s under the hood, Traefik ingress controller,
  built-in network policy enforcement. On a Rancher Manager downstream cluster,
  only [step 0.2](steps/phase-0.md#02-verify-cluster-access) and the ingress/TLS
  steps differ (flagged inline).
- PostgreSQL and nginx are pulled from public registries. The Python app is built
  locally — deliberately, since "build → deploy → iterate" is a core real-world
  skill.

!!! warning "Runtime caveat"
    Rancher Desktop defaults to `containerd`. Images built with `docker build`
    are invisible to k3s unless you switch to the `moby` engine or build with
    `nerdctl build`
    ([step 2.2](steps/phase-2.md#22-build-the-image-rancher-desktop-runtime-caveat)).

## How to use this tutorial

Work through the steps in order — each has **Goals**, **Concepts**, **Commands**,
and a **Verify** checkpoint. Start with
[Getting started](getting-started.md) to check prerequisites and scaffold the
repo, then begin at [Phase 0](steps/phase-0.md).
