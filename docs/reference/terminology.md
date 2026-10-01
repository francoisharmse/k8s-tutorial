# Terminology

The vocabulary you'll keep meeting — grouped by what the thing *is*. Terms
marked ★ appear somewhere in this tutorial.

## Core workload objects

| Term | What it is |
|------|-----------|
| **Pod** ★ | Smallest deployable unit — one or more containers sharing network + storage. You almost never create pods directly. |
| **Deployment** ★ | Declares N identical, replaceable pods; owns a ReplicaSet that keeps `desired == actual`. Rolling updates built in. |
| **ReplicaSet** | The controller a Deployment drives — maintains the replica count. Rarely managed directly. |
| **StatefulSet** ★ | Deployment for stateful workloads — stable pod names (`pg-postgresql-0`), ordered startup, per-pod PVC. |
| **DaemonSet** | One pod per node — log agents, CNI plugins, monitoring exporters. |
| **Job / CronJob** | Run-to-completion work / jobs on a schedule. |
| **Init container** | Container that runs *before* app containers start — migrations, waits. |
| **Sidecar** | Helper container sharing a pod — log shippers, service-mesh proxies. |

## Networking & traffic

| Term | What it is |
|------|-----------|
| **Service (ClusterIP)** ★ | Stable virtual IP + DNS name fronting a set of pods — the default type. |
| **Headless service** ★ | ClusterIP `None` — DNS returns pod IPs directly; StatefulSets use it for per-replica addressing. |
| **NodePort** | Service exposed on a port on every node — mostly superseded by ingress/LB. |
| **LoadBalancer** | Service that provisions a cloud LB. On local clusters usually `Pending` without MetalLB. |
| **Ingress** ★ | HTTP(S) routing rules (host/path → service) interpreted by an ingress controller. |
| **Ingress controller** ★ | The thing that *runs* the Ingress rules — Traefik on k3s, NGINX elsewhere. |
| **Gateway API** | Successor to Ingress — richer, role-oriented routing model. |
| **Endpoints / EndpointSlice** ★ | The list of Ready pod IPs behind a Service — `kubectl get endpoints`. |
| **CoreDNS** ★ | The cluster's DNS server — resolves `svc.namespace.svc.cluster.local`. |
| **kube-proxy** ★ | Node agent programming Service VIP → pod IP routing. |
| **CNI** | Container Network Interface — the pod-networking plugin layer (Calico, Cilium, Flannel…). |
| **NetworkPolicy** | Firewall rules for pod-to-pod traffic; needs a CNI that enforces them. |

## Config & state

| Term | What it is |
|------|-----------|
| **ConfigMap** ★ | Non-secret key/value config injected as env vars or files. |
| **Secret** ★ | Same mechanism for sensitive values — base64, *not* encryption. RBAC + encryption-at-rest are the real protection. |
| **Namespace** ★ | Logical scope inside a cluster — names, RBAC, and quotas are namespaced. |
| **PersistentVolume (PV)** ★ | A piece of storage provisioned in the cluster. |
| **PersistentVolumeClaim (PVC)** ★ | A pod's request for storage — binds to a PV. |
| **StorageClass** ★ | Template for dynamic PV provisioning — `local-path` on k3s, EBS on EKS. |
| **ServiceAccount** | Identity for pods; tokens mount into containers for API access. |
| **RBAC — Role/ClusterRole/Binding** | Who may do what, on which resources, where. |

## Control plane & node internals

| Term | What it is |
|------|-----------|
| **API server** ★ | The cluster's front door — everything talks to it; the only etcd writer. |
| **etcd** ★ | Distributed KV store holding all cluster state — desired *and* observed. |
| **Scheduler** ★ | Assigns unscheduled pods to nodes by scoring fit. |
| **Controller manager** ★ | Bundles the control loops (Deployment, StatefulSet, Job…). |
| **kubelet** ★ | Per-node agent — runs the pods the API assigns it, reports status. |
| **Container runtime** ★ | containerd/CRI-O — actually pulls images and runs containers. |
| **Probe (liveness/readiness/startup)** ★ | kubelet health checks — liveness restarts, readiness gates traffic, startup slows burn-in. |
| **QoS class** ★ | Guaranteed / Burstable / BestEffort — eviction priority derived from requests/limits. |
| **CRD + Operator** | Custom Resource Definition extends the API; an Operator is a controller that manages one. |
| **HPA / VPA** | Horizontal (replica count) / Vertical (resources) autoscalers. |

## Everyday tools

| Tool | What it is |
|------|-----------|
| **kubectl** ★ | The CLI client to the API server. `k` is the conventional alias. |
| **kubectx / kubens** | Fast context/namespace switching (`kubens` ≈ `config set-context --current --namespace=`). |
| **k9s** | Terminal UI for browsing/managing a cluster interactively. |
| **stern** | Multi-pod log tailing — `stern app` streams every matching pod. |
| **nerdctl** ★ | Docker-like CLI for containerd — Rancher Desktop's build tool (`--namespace k8s.io`). |
| **Lens / OpenLens** | GUI cluster dashboard. |
| **Skaffold / Tilt** | Local dev loops — build → deploy → stream on file change. |

## Packaging & templating

| Tool | What it is |
|------|-----------|
| **Helm** ★ | Package manager — charts (templated manifest bundles), releases, values files, `helm install/upgrade/rollback`. |
| **Kustomize** | Overlay engine built into `kubectl -k` — patches base manifests per environment, no templating language. |
| **Chart** ★ | A Helm package: `Chart.yaml` + templates + `values.yaml` defaults. |
| **values.yaml / `-f` file** ★ | Your overrides merged over chart defaults at render time. |
| **OCI registry (charts/images)** | Container registries also store charts/images as artifacts — `oci://…`. |
| **Artifact Hub** | The public index for Helm charts (and operators, OPA policies…). |

## GitOps & delivery

| Tool | What it is |
|------|-----------|
| **Argo CD** | GitOps controller — watches a git repo and keeps the cluster synced to the manifests in it. Pull model, rich UI. |
| **Flux** | The other big GitOps controller — composable toolkit style, CRD-driven. |
| **GitOps** | The pattern: git is the source of truth; a controller reconciles cluster state to it. No human `apply`. |
| **Tekton** | Kubernetes-native CI/CD pipelines as CRDs. |
| **cert-manager** | Automates TLS cert issuance/renewal (Let's Encrypt etc.) as CRDs. |
| **External Secrets Operator** | Syncs Vault/AWS SM/etc. secrets into Kubernetes Secrets. |

## Observability & ops

| Tool | What it is |
|------|-----------|
| **metrics-server** ★ | Lightweight metrics API powering `kubectl top`. |
| **Prometheus / kube-prometheus-stack** | Metrics collection + alerting; the stack chart bundles Grafana + Alertmanager. |
| **Grafana** | Dashboards over Prometheus (and friends). |
| **Loki / EFK** | Log aggregation stacks (Loki+Grafana, or Elastic+Fluentd+Kibana). |
| **Velero** | Cluster backup/restore — objects *and* volumes. |
| **OpenTelemetry** | Tracing/metrics instrumentation standard, collector runs in-cluster. |

## Local clusters & dev

| Tool | What it is |
|------|-----------|
| **Rancher Desktop** ★ | This tutorial's cluster — desktop k3s + containerd/moby choice. |
| **k3s** ★ | Lightweight CNCF Kubernetes — control plane in one binary; what Rancher Desktop runs. |
| **kind** | Kubernetes IN Docker — nodes as containers; the classic CI/test cluster. |
| **minikube** | The original local cluster — VM or container driver, `minikube tunnel` for LBs. |
| **k3d** | k3s inside Docker — fast multi-node local clusters. |
| **MicroK8s** | Canonical's snap-packaged Kubernetes. |
| **Docker Desktop (k8s)** | Docker Desktop's built-in single-node cluster option. |

## Distributions & managed platforms

| Platform | What it is |
|----------|-----------|
| **OpenShift** ★ | Red Hat's enterprise Kubernetes — namespaces become *Projects*, `oc` CLI = kubectl + extras, built-in registry, builds, and stricter security defaults (SCC). |
| **EKS** | AWS managed Kubernetes — control plane hosted, you manage nodes (or Fargate). |
| **AKS** | Azure managed Kubernetes — control plane free, nodes are your VMs. |
| **GKE** | Google managed Kubernetes — the oldest managed offering; Autopilot mode runs nodes for you. |
| **Rancher (Manager)** | Fleet manager — provisions and operates many clusters (RKE/RKE2/k3s/distro-managed) from one UI/API. |
| **Tanzu** | VMware's Kubernetes platform (vSphere-integrated, now under Broadcom). |
| **OKD** | The open-source upstream of OpenShift. |
| **LKE / VKE / DOKS / etc.** | Linode, Vultr, DigitalOcean managed clusters — smaller clouds, same API. |

## Concepts that aren't objects

| Term | What it is |
|------|-----------|
| **Imperative vs declarative** ★ | Command actions (`create`, `run`) vs desired-state manifests (`apply`). |
| **Desired state / control loop** ★ | You declare intent; controllers continuously reconcile reality toward it. |
| **Context** ★ | kubeconfig entry = cluster + credentials + default namespace. `use-context` switches between them. |
| **Labels & selectors** ★ | Key/value tags on objects; Services/Deployments select pods by them. |
| **Annotations** | Non-identity metadata — docs, tooling hints, `last-applied-configuration`. |
| **imagePullPolicy** ★ | `Always`/`IfNotPresent`/`Never` — when kubelet pulls vs uses cached images. |
| **Rollout** ★ | A Deployment's rolling update; `rollout status/history/undo/restart`. |
| **OOMKill** ★ | Kernel kills a container over `limits.memory` — shows as an event + restart. |
| **Taints & tolerations** | Node-side repulsion vs pod-side permission — how control-plane nodes stay clean. |
| **Canary / blue-green** | Deployment strategies — shift a slice of traffic / swap two environments. |
| **Multi-tenancy** | Multiple teams/apps sharing one cluster — namespaces + RBAC + quotas are the primitives. |
