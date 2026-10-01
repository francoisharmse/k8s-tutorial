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

    *Why:* the cheapest end-to-end test — if kubectl can reach the API server,
    this prints both versions. It also exposes version *skew* between your
    client and the cluster.

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

    *Why:* kubectl multiplexes clusters — the same binary can talk to a local
    k3s, minikube, or a production cluster. Always confirm *which* cluster
    you're about to touch before running anything.

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

    *Why:* everything after this targets `rancher-desktop`. Getting contexts
    wrong is how people accidentally run commands against the wrong cluster.

    ```bash
    kubectl config use-context rancher-desktop
    ```

    ??? info "Expected output"

        `Switched to context "rancher-desktop".` — every command from here on
        targets this context unless you override it with `--context`.

4.  List the cluster's nodes:

    *Why:* nodes are the machines your workloads land on. `get nodes` is the
    cluster health check; `-o wide` adds IPs, OS, and container runtime —
    the facts you reach for when pods won't schedule.

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

    *Why:* `-A` (all namespaces) shows the system workloads too — it's both a
    health check and a lesson: DNS, ingress, and storage are just pods in
    `kube-system`, same as the ones you'll deploy.

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

    *Why:* you'll deploy PostgreSQL via a Helm chart in step 1.2 — better to
    discover a missing install now than mid-step.

    ```bash
    helm version
    ```

    ??? info "Expected output"

        `version.BuildInfo{Version:"v3.x.x", GitCommit:"…", GoVersion:"…"}` —
        just proves helm works; the version prints inside `BuildInfo`.

    ??? tip "helm: command not found? Install it"

        === "macOS — Homebrew"

            ```bash
            brew install helm
            ```

        === "Windows — winget"

            ```powershell
            winget install Helm.Helm
            ```

        === "Windows — Chocolatey"

            ```powershell
            choco install kubernetes-helm
            ```

        === "Windows — Scoop"

            ```powershell
            scoop install helm
            ```

        === "Debian/Ubuntu — apt"

            ```bash
            curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | \
              sudo tee /usr/share/keyrings/helm.gpg > /dev/null
            echo "deb [signed-by=/usr/share/keyrings/helm.gpg] \
              https://baltocdn.com/helm/stable/debian/ all main" | \
              sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
            sudo apt update && sudo apt install helm
            ```

        === "Fedora — dnf"

            ```bash
            sudo dnf install helm
            ```

        === "Linux — Snap"

            ```bash
            sudo snap install helm --classic
            ```

        === "Any OS — official script"

            ```bash
            curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
            ```

        All of these install the `helm` binary on your `PATH` — re-run
        `helm version` afterwards to confirm.

7.  Browse the API surface:

    *Why:* this is the catalog of everything kubectl can manage — discoverable
    instead of memorized. It answers "does `hpa` have a shortname?" and "is a
    `clusterrole` namespaced?" without leaving the terminal.

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

#### Mental model — clusters, contexts, namespaces

These three words sound alike but live in different places — a classic early
confusion:

| Concept | Where it lives | List it with |
|---------|----------------|--------------|
| **Cluster** | kubeconfig — an API endpoint + CA cert | `kubectl config get-clusters` |
| **Context** | kubeconfig — cluster + credentials + default namespace | `kubectl config get-contexts` |
| **Namespace** | *inside* a cluster — scopes your objects | `kubectl get namespaces` |

Explore the difference yourself:

1.  List the cluster connections kubectl knows:

    *Why:* contexts point *at* clusters — this shows the API endpoints your
    kubeconfig can reach.

    ```bash
    kubectl config get-clusters
    ```

    ??? info "Expected output"

        ```bash
        NAME
        rancher-desktop
        minikube              # (1)!
        ```

        1.  These are kubeconfig *entries*, not running machines — `minikube`
            lists even if that cluster is stopped or deleted.

2.  List the namespaces inside the **current** cluster:

    *Why:* namespaces are created *inside* a cluster and scope the objects in
    it — they say nothing about connections.

    ```bash
    kubectl get namespaces
    ```

    ??? info "Expected output"

        ```bash
        NAME              STATUS   AGE   # (1)!
        default           Active   31m
        kube-node-lease   Active   31m
        kube-public       Active   31m
        kube-system       Active   31m
        playground        Active   16s   # (2)!
        ```

        1.  Columns — `STATUS`: `Active` or `Terminating` · `AGE`: time since
            created.
        2.  `playground` exists if you ran step 0.3. The other four ship with
            every cluster: `kube-system` holds cluster services, `default` is
            where un-namespaced commands land.

3.  Try switching context to a namespace — it fails on purpose:

    *Why:* proves contexts and namespaces are different things — a context is
    a kubeconfig entry; you can't `use-context` a namespace name.

    ```bash
    kubectl config use-context playground
    ```

    ??? failure "Expected output"

        `error: no context exists with the name: "playground"` — `playground`
        is a *namespace* inside the cluster, not a kubeconfig context.

    What you probably meant — default the **current context** to a namespace:

    ```bash
    kubectl config set-context --current --namespace=playground
    ```

    ??? info "Expected output"

        `Context "rancher-desktop" modified.` — this fills the `NAMESPACE`
        column in `get-contexts`, so later commands can drop `-n playground`.
        (Step [1.1](phase-1.md#11-namespace--secrets) uses exactly this trick.)

    ??? tip "How OpenShift handles this — Projects"

        OpenShift (Red Hat's Kubernetes distribution) calls namespaces
        **Projects**. A `Project` *is* a namespace — same object underneath —
        with extra metadata (display name, description) and default RBAC
        wiring on top.

        Two differences you'd notice:

        - **Creation:** `oc new-project playground` instead of
          `kubectl create namespace` — and it's *self-service*: users can
          request projects subject to admin-set quotas, where raw
          `kubectl create ns` typically needs elevated rights.
        - **Switching:** the `oc` CLI (kubectl + OpenShift verbs) makes
          project switching first-class:

          ```bash
          oc project playground
          ```

          → `Now using project "playground" on server "https://…".`

          This works where `kubectl config use-context playground` failed —
          under the hood it does exactly what
          `kubectl config set-context --current --namespace=playground` does:
          edits the current context's namespace field. Related verbs:
          `oc projects` lists what you can access, `oc project` (no args)
          shows the current one.

        Same mental model — context still holds cluster + creds + namespace;
        OpenShift just gives the namespace-switch a dedicated verb.

??? warning "Common errors & fixes"
    **`error: unknown flag: --short`** — the `--short` flag was deprecated in
    kubectl 1.28 and **removed in 1.30**. Run plain `kubectl version` — it
    prints client and server versions. For detail: `kubectl version -o json`.

    **`The connection to the server localhost:8080 was refused`** — the cluster
    isn't running. Start Rancher Desktop and confirm *Preferences → Kubernetes →
    Enable Kubernetes* is checked.

    **`error: no context exists with the name "…"`** — two causes. If the name
    is `rancher-desktop`: your kubeconfig is missing it — enable Kubernetes in
    Rancher Desktop (it writes `~/.kube/config`) and re-run
    `kubectl config get-contexts`. If the name is a *namespace* (e.g.
    `playground`): contexts aren't namespaces — use
    `kubectl config set-context --current --namespace=<ns>` instead.

    **`error: invalid resource name ".": may not be '.'`** — a stray `.` slipped
    in (e.g., `kubectl get nodes .`). kubectl reads it as a resource name —
    drop it.

    **`helm: command not found`** — see the *Install it* dropdown under
    command 6 above (`brew install helm` on macOS).

!!! success "Verify"
    Node shows `Ready`; `kube-system` pods `Running`.

---

## 0.3 — Imperative playground

!!! info "Imperative vs declarative — two ways to drive kubectl"

    **Imperative** = tell the cluster *what to do*, one action at a time:
    `kubectl create`, `kubectl run`, `kubectl delete`, `kubectl scale`. You're
    the control loop — nothing is written down, so there's no record of intent
    and no easy way to repeat or diff the result.

    **Declarative** = describe the *desired end state* in a YAML manifest and
    let `kubectl apply` reconcile it. The spec becomes the source of truth:
    it's repeatable, diffable, versionable in git, and controllers keep
    reality converging toward it.

    Rule of thumb: imperative for **learning, debugging, and throwaway
    experiments** (this step) — declarative for **anything that should
    survive past the terminal session** (every manifest phase from
    [Phase 1](phase-1.md) onward).

**Goals:** Learn the core objects hands-on before declarative YAML.

**Concepts:** Pods, namespaces, describe/logs/exec, `kubectl explain`.

Run these in order. Expand **ⓘ Expected output** under each command to compare
with yours — the `+` markers inside the output explain every column and status.

1.  Create a scratch namespace:

    *Why:* namespaces scope everything that follows. A disposable `playground`
    keeps experiments from polluting other namespaces — and deleting it at the
    end cleans up in one shot.

    ```bash
    kubectl create namespace playground
    ```

    ??? info "Expected output"

        ```bash
        namespace/playground created      # (1)!
        ```

        1.  kubectl confirms creation as `resource/name created` — that exact
            pattern is how you'll address it later (`kubectl get ns playground`).

2.  Run a pod imperatively:

    *Why:* `kubectl run` is the fastest way to get a workload up without YAML —
    good for experiments, debugging, and throwaway tools. (Real apps come from
    Deployments, covered later.)

    ```bash
    kubectl run demo --image=nginx:1.27 -n playground
    ```

    ??? info "Expected output"

        ```bash
        pod/demo created                  # (1)!
        ```

        1.  The pod object exists — but the image still has to be *pulled* in
            the background. The pod won't be `Running` until that finishes.

3.  Watch the pod lifecycle live:

    *Why:* `-w` streams changes in real time — you see the full lifecycle
    (`Pending` → `ContainerCreating` → `Running`) instead of a snapshot.

    ```bash
    kubectl get pods -n playground -w
    ```

    ??? info "Expected output"

        ```bash
        NAME   READY   STATUS              RESTARTS   AGE     # (1)!
        demo   0/1     Pending             0          2s
        demo   0/1     ContainerCreating   0          4s      # (2)!
        demo   1/1     Running             0          15s     # (3)!
        ```

        1.  Columns — `READY`: containers ready / total · `STATUS`: lifecycle
            phase · `RESTARTS`: container restart count · `AGE`: time since
            the pod was scheduled.
        2.  `ContainerCreating` = image pulling + container starting. The most
            common stall point — slow pulls or a bad image name (typo →
            `ErrImagePull`/`ImagePullBackOff` appears here).
        3.  `1/1 Running` — all containers up. Ctrl+C exits the *watch*; the
            pod keeps running.

4.  Inspect the pod in detail:

    *Why:* `describe` is the diagnostic command — full spec, status,
    conditions, and the **Events** log of what the cluster *did*. It's the
    first thing to run whenever a pod misbehaves.

    ```bash
    kubectl describe pod demo -n playground
    ```

    ??? info "Expected output (trimmed)"

        ```bash
        Name:         demo
        Namespace:    playground
        Status:       Running
        Containers:
          demo:
            Image:    nginx:1.27
            State:    Running
            Ready:    True
        Conditions:
          Type            Status
          Ready           True                                   # (1)!
        Events:
          Type    Reason     Age   From               Message
          ----    ------   ----  ----               -------
          Normal  Scheduled  2m   default-scheduler  Successfully assigned playground/demo to lima-rancher-desktop  # (2)!
          Normal  Pulling    2m   kubelet            Pulling image "nginx:1.27"                                   # (3)!
          Normal  Pulled     1m   kubelet            Successfully pulled image "nginx:1.27"
          Normal  Started    1m   kubelet            Started container demo                                        # (4)!
        ```

        1.  `Conditions` = health gates the pod must pass — `Ready` is what
            Services check before routing traffic.
        2.  The scheduler's decision — which node got the pod. `FailedScheduling`
            here = no node fits (resources, taints).
        3.  Image pull starts — a common failure point
            (`ErrImagePull`/`ImagePullBackOff` events).
        4.  Events are the story of *what Kubernetes did* — read them
            bottom-up when triaging.

5.  Read the app's own logs:

    *Why:* `describe` tells you what *Kubernetes* did; `logs` tells you what
    the *application* said. Knowing which to check is the core debugging split.

    ```bash
    kubectl logs demo -n playground
    ```

    ??? info "Expected output"

        ```bash
        /docker-entrypoint.sh: Configuration complete; ready for start up
        2026/09/30 10:00:00 [notice] 1#1: nginx/1.27.x             # (1)!
        ```

        1.  nginx startup lines on stdout — you'll also see access-log entries
            here once requests hit it. Empty output isn't an error, just means
            the app has been quiet.

6.  Get a shell inside the container:

    *Why:* `exec -it` drops you into the container's own environment — run
    `ps`, `ls`, `wget localhost` to verify the app as the cluster sees it.
    `-i -t` makes it interactive; `--` separates kubectl flags from the command.

    ```bash
    kubectl exec -it demo -n playground -- /bin/sh
    ```

    ??? info "Expected output"

        ```bash
        / # hostname
        demo                                      # (1)!
        / # exit                                  # (2)!
        ```

        1.  Inside the container, `hostname` = the pod name — a quick proof
            you're inside it.
        2.  `exit` leaves the shell; the pod keeps running. If `/bin/sh`
            doesn't exist in the image, try `/bin/bash`.

7.  Look up field docs without leaving the terminal:

    *Why:* `kubectl explain` is the built-in API reference — it answers "what
    fields exist and what do they mean?" for any resource, which beats
    guessing YAML keys.

    ```bash
    kubectl explain pod.spec.containers
    ```

    ??? info "Expected output"

        ```bash
        KIND:     Pod
        VERSION:  v1

        FIELD:    containers <[]Container>                        # (1)!

        DESCRIPTION:
            List of containers belonging to the pod. ...          # (2)!
        ```

        1.  `<[]Container>` = a **list** of container objects — that's why
            `containers:` takes `- name:` items in YAML.
        2.  Keep drilling: `pod.spec.containers.image`,
            `pod.spec.containers.resources`, …

8.  Tear everything down:

    *Why:* namespace deletion cascades — every object inside `playground`
    dies with it. The fastest way to reset a scratch environment.

    ```bash
    kubectl delete namespace playground
    ```

    ??? info "Expected output"

        ```bash
        namespace "playground" deleted      # (1)!
        ```

        1.  The `demo` pod goes with it — no separate `delete pod` needed.
            Deletion takes a few seconds while children terminate.

!!! success "Verify"
    You can explain the difference between `describe` (what happened) and
    `logs` (what the app said).
