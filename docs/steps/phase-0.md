# Phase 0 — Environment & Cluster Orientation

## 0.1 — Scaffold the project directory

**Goals:** Create the directory layout you'll work in for the whole tutorial.

**Concepts:** Project layout conventions; optional single-branch + tag workflow
if you choose to track your work in git.

```bash
mkdir k8s && cd k8s                                        # (1)
mkdir -p steps app static db scripts \                     # (2)
  deploy/manifests/{app,db,ingress,netpol,web} \
  deploy/charts
```

1.  Creates the working dir and enters it — silence means success.
2.  `mkdir -p` builds the whole tree in one shot; `{a,b,c}` brace expansion
    creates the five manifest dirs at once. No output on success.

!!! info "Git tracking is optional"
    Everything in this tutorial works on a plain directory of files — the
    cluster never sees git. The git commands below are **only needed if you
    want to commit and track your progress in a repo** (checkpoint tags,
    `git checkout` savepoints). If you prefer to work completely locally
    without git, skip them — nothing else in the tutorial depends on them.

If you do want git tracking (recommended — it gives you savepoints):

```bash
git init -b main                                           # (1)

# git doesn't track empty dirs — placeholders keep the skeleton visible:
find . -type d -empty -exec touch {}/.gitkeep \;           # (2)
```

1.  `Initialized empty Git repository in …/k8s/.git/` — `-b main` names the
    default branch `main`.
2.  No output — drops an empty `.gitkeep` file into every directory that has
    no content yet, so the skeleton survives the commit.

Then add a `.gitignore` covering your editor/OS noise plus these
tutorial-specific rules — real Secrets never get committed (reinforced in
[step 6.1](phase-6.md#61-secrets-encryption-at-rest)):

```gitignore
secrets.yaml            # secrets.example.yaml stays tracked
*-key.pem               # mkcert/openssl private keys (step 4.2)
dump.sql                # pg_dump output (step 7.4)
```

```bash
git add -A && git commit -m "Scaffold tutorial repo"       # (1)
git tag phase-0                                            # (2)
```

1.  `[main (root-commit) <hash>] Scaffold tutorial repo` — followed by a
    file/insertion count summary.
2.  No output — the `phase-0` tag now marks this commit as a savepoint.

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
kubectl version                             # client + server versions (1)
kubectl config get-contexts                 # confirm you're on rancher-desktop (2)
kubectl config use-context rancher-desktop  # if needed (3)
kubectl get nodes -o wide                   # nodes, IPs, container runtime (4)
kubectl get pods -A                         # all system pods (5)
helm version                                # (6)
kubectl api-resources | head -30            # discover object types (7)
```

1.  `Client Version: v1.xx.x` and `Server Version: v1.32.x+k3s1` — the `+k3s1`
    suffix confirms the server is k3s (Rancher Desktop's distribution).
2.  Lists every context in `~/.kube/config`; `*` marks the active one:

    ```text
    CURRENT   NAME              CLUSTER           AUTHINFO          NAMESPACE
              minikube          minikube          minikube          default
    *         rancher-desktop   rancher-desktop   rancher-desktop
    ```

3.  `Switched to context "rancher-desktop".` — only needed if `*` wasn't
    already on it. All later commands now default to this context.
4.  One line per node — Rancher Desktop runs a single-node cluster:

    ```text
    NAME                   STATUS   ROLES                  AGE   VERSION
    lima-rancher-desktop   Ready    control-plane,master   37s   v1.32.3+k3s1
    ```

5.  Pods in **all** namespaces — expect `coredns`, `traefik`,
    `local-path-provisioner`, `metrics-server` under `kube-system`.
6.  `version.BuildInfo{Version:"v3.x", …}` — just proves helm is installed.
7.  A long table of every API type the cluster serves — `head -30` trims it.
    Handy later: `kubectl api-resources | grep deploy`.

??? warning "Common errors & fixes"
    **`error: unknown flag: --short`** — the `--short` flag was deprecated in
    kubectl 1.28 and **removed in 1.30**. Run plain `kubectl version` — it
    prints client and server versions. For detail: `kubectl version -o json`.

    **`The connection to the server localhost:8080 was refused`** — the cluster
    isn't running. Start Rancher Desktop and confirm *Preferences → Kubernetes →
    Enable Kubernetes* is checked.

    **`error: no context exists with the name "rancher-desktop"`** — your
    kubeconfig is missing the context. Rancher Desktop writes `~/.kube/config`
    when Kubernetes is enabled; enable it (or restart Rancher Desktop) and
    re-run `kubectl config get-contexts`.

    **`error: invalid resource name ".": may not be '.'`** — a stray `.` slipped
    in (e.g., `kubectl get nodes .`). kubectl reads it as a resource name —
    drop it.

    **`helm: command not found`** — `brew install helm`.

!!! success "Verify"
    Node shows `Ready`; `kube-system` pods `Running`.

---

## 0.3 — Imperative playground

**Goals:** Learn the core objects hands-on before declarative YAML.

**Concepts:** Pods, namespaces, describe/logs/exec, `kubectl explain`.

```bash
kubectl create namespace playground                            # (1)
kubectl run demo --image=nginx:1.27 -n playground                # (2)
kubectl get pods -n playground -w                                # (3) watch — Ctrl+C to stop
kubectl describe pod demo -n playground                          # (4) events + conditions
kubectl logs demo -n playground                                  # (5)
kubectl exec -it demo -n playground -- /bin/sh                   # (6)
kubectl explain pod.spec.containers                              # (7) built-in API docs
kubectl delete namespace playground                              # (8) cascades everything
```

1.  `namespace/playground created` — a fresh, empty scope for experimenting.
2.  `pod/demo created` — the first run also pulls the `nginx:1.27` image.
3.  Streams live status: `Pending` → `ContainerCreating` → `Running`.
    Ctrl+C stops watching — the pod keeps running.
4.  Full spec, status, and an **Events** section at the bottom — your first
    stop whenever something's wrong.
5.  nginx's startup/access logs — probably empty until you send it a request.
6.  An interactive shell *inside* the container (`/ #` prompt); `exit` to leave.
7.  Prints that field's documentation inline — works on any `resource.field`.
8.  `namespace "playground" deleted` — everything inside it goes with it.

!!! success "Verify"
    You can explain the difference between `describe` (what happened) and
    `logs` (what the app said).
