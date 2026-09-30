# Phase 0 — Environment & Cluster Orientation

## 0.1 — Scaffold the project directory

**Goals:** Create the directory layout you'll work in for the whole tutorial.

**Concepts:** Project layout conventions; optional single-branch + tag workflow
if you choose to track your work in git.

```bash
mkdir k8s && cd k8s
mkdir -p steps app static db scripts \
  deploy/manifests/{app,db,ingress,netpol,web} \
  deploy/charts
```

!!! info "Git tracking is optional"
    Everything in this tutorial works on a plain directory of files — the
    cluster never sees git. The git commands below are **only needed if you
    want to commit and track your progress in a repo** (checkpoint tags,
    `git checkout` savepoints). If you prefer to work completely locally
    without git, skip them — nothing else in the tutorial depends on them.

If you do want git tracking (recommended — it gives you savepoints):

```bash
git init -b main

# git doesn't track empty dirs — placeholders keep the skeleton visible:
find . -type d -empty -exec touch {}/.gitkeep \;
```

Then add a `.gitignore` covering your editor/OS noise plus these
tutorial-specific rules — real Secrets never get committed (reinforced in
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
    `find . -type d` shows the
    [repo layout](../getting-started.md#repo-layout). If you're using git:
    `git log --oneline` shows the scaffold commit — from here on, tag at each
    phase boundary (`git tag phase-1`, …) per
    [Git strategy](../getting-started.md#git-strategy-checkpoint-tags-not-branches).

---

## 0.2 — Verify cluster access

**Goals:** Confirm kubectl talks to the local cluster; understand contexts.

**Concepts:** kubeconfig, contexts, control plane vs worker nodes.

!!! tip "Optional: alias `kubectl` → `k`"
    Every command in this tutorial spells out `kubectl` for clarity — but most
    people alias it to `k` and never look back. One-time setup, per shell:

    === "zsh (macOS default)"

        ```bash
        echo 'alias k=kubectl' >> ~/.zshrc && source ~/.zshrc
        # keep tab-completion working on the alias:
        echo 'source <(kubectl completion zsh)' >> ~/.zshrc
        echo 'compdef k=kubectl' >> ~/.zshrc
        ```

    === "bash"

        ```bash
        echo 'alias k=kubectl' >> ~/.bashrc && source ~/.bashrc
        # on macOS the login file is ~/.bash_profile instead
        # completion: complete -o default -F __start_kubectl k
        ```

    === "fish"

        ```bash
        echo 'alias k=kubectl' >> ~/.config/fish/config.fish
        ```

    === "PowerShell (Windows)"

        ```powershell
        Set-Alias k kubectl                                # current session
        Add-Content $PROFILE 'Set-Alias k kubectl'         # persist
        ```

    === "CMD (Windows)"

        ```bat
        doskey k=kubectl $*    :: current session only
        ```

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
