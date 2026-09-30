# Phase 0 — Environment & Cluster Orientation

## 0.1 — Scaffold the repo

**Goals:** Create the directory layout; set up the git checkpoint-tag workflow.

**Concepts:** Single-branch + tags workflow, `.gitkeep` placeholders for empty
dirs, keeping secrets out of git from day one.

```bash
mkdir k8s-tutorial && cd k8s-tutorial
git init -b main

mkdir -p steps app static db scripts \
  deploy/manifests/{app,db,ingress,netpol,web} \
  deploy/charts

# git doesn't track empty dirs — placeholders keep the skeleton visible:
find . -type d -empty -exec touch {}/.gitkeep \;
```

Add a `.gitignore` covering your editor/OS noise plus these tutorial-specific
rules — real Secrets never get committed (reinforced in
[step 6.1](phase-6.md#61-secrets-encryption-at-rest)):

```gitignore
secrets.yaml            # secrets.example.yaml stays tracked
*-key.pem               # mkcert/openssl private keys (step 4.2)
dump.sql                # pg_dump output (step 7.4)
```

```bash
git add -A && git commit -m "Scaffold tutorial repo"
git tag phase-0
```

!!! success "Verify"
    `git log --oneline` shows the scaffold commit; `find . -type d` matches the
    [repo layout](../getting-started.md#repo-layout). From here on, tag at each
    phase boundary (`git tag phase-1`, …) — see
    [Git strategy](../getting-started.md#git-strategy-checkpoint-tags-not-branches).

---

## 0.2 — Verify cluster access

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

!!! success "Verify"
    Node shows `Ready`; `kube-system` pods `Running`.

---

## 0.3 — Imperative playground

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

!!! success "Verify"
    You can explain the difference between `describe` (what happened) and
    `logs` (what the app said).
