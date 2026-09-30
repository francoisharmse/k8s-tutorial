# Phase 8 — Advanced / Optional

## 8.1 — Observability stack (Prometheus + Grafana)

**Goals:** Metrics-based insight into the whole cluster.

**Concepts:** kube-prometheus-stack, ServiceMonitor, scrape targets, dashboards.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install mon prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
kubectl port-forward svc/mon-grafana -n monitoring 3000:80   # admin / prom-operator
```

Add a `/metrics` endpoint (prometheus-client) to the FastAPI app + a
ServiceMonitor → app metrics appear in Grafana alongside cluster metrics.

!!! success "Verify"
    Grafana dashboards show pod CPU/mem; app request metrics visible.

---

## 8.2 — GitOps preview

**Goals:** See how Helm + git replaces manual `kubectl apply` in production.

**Concepts:** Declarative desired state, drift reconciliation, Fleet/ArgoCD.

Point **Rancher Fleet** (bundled with Rancher) or ArgoCD at this repo — upgrades
become `git push`. Rancher Desktop alone doesn't include the Fleet UI; this step
is conceptual + optional install.

---

## 8.3 — Teardown & troubleshooting playbook

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
