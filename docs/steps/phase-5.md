# Phase 5 — IaC: Helm-ify Everything

## Step 16 — Build the umbrella chart

**Goals:** Convert all hand-applied manifests into one versioned,
parameterizable chart.

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

Move all manifests from `deploy/manifests/` into `templates/`, parameterizing
image tags, DB settings, ingress host, and resources through `values.yaml`. Add
`values-dev.yaml` / `values-prod.yaml` to model environment promotion. Add a
checksum annotation on the web Deployment so ConfigMap changes auto-roll pods:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/web-configmap.yaml") . | sha256sum }}
```

!!! success "Verify"
    `helm template` output equals what you applied by hand.

---

## Step 17 — Migrate to Helm-managed; release lifecycle

**Goals:** Own the stack as a Helm release; learn upgrade/rollback.

**Concepts:** Releases, release history secrets, `--set` vs `-f`, rollback
semantics.

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

!!! success "Verify"
    `helm history` shows the upgrade and rollback revisions.
