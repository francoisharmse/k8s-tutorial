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

Run these in order. Expand **ⓘ Expected output** under each command to compare
with yours — the `+` markers inside the output explain every column and status.

1.  Check client + server versions:

    ```bash
    kubectl version
    ```

    ??? info "Expected output"

        ```bash
        Client Version: v1.34.x
        Kustomize Version: v5.x.x
        Server Version: v1.32.x+k3s1      # (1)!
        ```

        1.  `Server Version` is what the cluster runs — the `+k3s1` suffix
            means it's **k3s**, Rancher Desktop's bundled distribution.

2.  List the contexts in your kubeconfig:

    ```bash
    kubectl config get-contexts
    ```

    ??? info "Expected output"

        ```bash
        CURRENT   NAME              CLUSTER           AUTHINFO          NAMESPACE   # (1)!
                  minikube          minikube          minikube          default
        *         rancher-desktop   rancher-desktop   rancher-desktop               # (2)!
        ```

        1.  Columns — `CURRENT`: `*` marks the active context · `NAME`: the
            alias you pass to `--context` · `CLUSTER`: which cluster entry it
            targets · `AUTHINFO`: which credentials it uses · `NAMESPACE`:
            default namespace for commands (empty = cluster default).
        2.  `*` on `rancher-desktop` — already active, so the next command is
            a no-op for you.

3.  Switch context — only needed if `*` wasn't on `rancher-desktop`:

    ```bash
    kubectl config use-context rancher-desktop
    ```

    ??? info "Expected output"

        `Switched to context "rancher-desktop".` — every command from here on
        targets this context unless you override it with `--context`.

4.  List the cluster's nodes:

    ```bash
    kubectl get nodes -o wide
    ```

    ??? info "Expected output"

        ```bash
        NAME                   STATUS   ROLES                  AGE   VERSION       # (1)!
        lima-rancher-desktop   Ready    control-plane,master   37s   v1.32.3+k3s1  # (2)!
        ```

        1.  Columns — `NAME`: node name · `STATUS`: `Ready` = kubelet healthy
            (`NotReady` under pressure/network loss) · `ROLES`: `control-plane`
            means it runs the API server + etcd · `AGE`: time since the node
            joined · `VERSION`: kubelet version. `-o wide` adds
            `INTERNAL-IP`, `OS-IMAGE`, `KERNEL`, `RUNTIME`.
        2.  Single node — Rancher Desktop runs a one-node k3s cluster;
            `lima-` is the Lima VM it lives in.

5.  List every pod in the cluster:

    ```bash
    kubectl get pods -A
    ```

    ??? info "Expected output"

        ```bash
        NAMESPACE     NAME                              READY   STATUS      RESTARTS   AGE   # (1)!
        kube-system   coredns-…                         1/1     Running     0          2m
        kube-system   helm-install-traefik-…            0/1     Completed   0          2m
        kube-system   local-path-provisioner-…          1/1     Running     0          2m
        kube-system   metrics-server-…                  1/1     Running     0          2m
        kube-system   traefik-…                         1/1     Running     0          2m    # (2)!
        ```

        1.  Columns — `NAMESPACE`: owning namespace · `READY`: containers
            ready / total · `STATUS`: lifecycle state (`Running`,
            `Completed`, `CrashLoopBackOff`, `ImagePullBackOff`, …) ·
            `RESTARTS`: container restart count · `AGE`: time since scheduled.
        2.  A healthy k3s baseline — everything lives in `kube-system`: DNS
            (`coredns`), ingress (`traefik`), storage (`local-path-provisioner`),
            `kubectl top` data (`metrics-server`).

6.  Confirm helm is installed:

    ```bash
    helm version
    ```

    ??? info "Expected output"

        `version.BuildInfo{Version:"v3.x.x", GitCommit:"…", GoVersion:"…"}` —
        just proves helm works; the version prints inside `BuildInfo`.

7.  Browse the API surface:

    ```bash
    kubectl api-resources | head -30
    ```

    ??? info "Expected output"

        ```bash
        NAME                    SHORTNAMES   APIVERSION   NAMESPACED   KIND      # (1)!
        bindings                             v1           true         Binding
        componentstatuses       cs           v1           false        ComponentStatus
        configmaps              cm           v1           true         ConfigMap
        endpoints               ep           v1           true         Endpoints
        namespaces              ns           v1           false        Namespace
        nodes                   no           v1           false        Node
        pods                    po           v1           true         Pod        # (2)!
        services                svc          v1           true         Service    # (3)!
        ```

        1.  Columns — `NAME`: plural resource name for `kubectl get` ·
            `SHORTNAMES`: aliases you can type instead · `APIVERSION`: API
            group/version · `NAMESPACED`: whether objects live inside a
            namespace · `KIND`: the type name for YAML `kind:` fields.
        2.  `po` works anywhere `pods` does: `kubectl get po`.
        3.  `NAMESPACED: false` resources (nodes, namespaces, PVs) don't take
            `-n` — they're cluster-scoped.

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
