# Phase 3 — Web Tier (nginx)

## 3.1 — nginx deployment

**Goals:** Serve the tutorial UI; reverse-proxy API calls to the app tier.

**Concepts:** ConfigMap-mounted config, reverse proxy, multi-tier request flow.

Run these in order. Expand **ⓘ INFO** under each command for the rationale and
expected output — the `+` markers explain every column and status.

1.  Build the web image — pick the tab matching your engine:

    === "containerd — nerdctl (default)"

        ```bash
        nerdctl --namespace k8s.io build -t k8s-tutorial-web:0.1.0 ./static
        ```

    === "dockerd (moby) — docker"

        ```bash
        docker build -t k8s-tutorial-web:0.1.0 ./static
        ```

    ??? info "INFO"

        ??? question "Why?"

            same runtime-namespaces story as step 2.2 — containerd builds
            must land in the `k8s.io` namespace for k3s to see them;
            dockerd shares its store directly. The `static/` dir carries
            `nginx.conf`, a Dockerfile, and the UI assets baked into the
            image.

        ??? info "Expected output"

            Same Buildkit progress as 2.2 — `FINISHED` plus an
            `unpackaging`/`writing image` line confirms the image landed.

2.  Apply the web manifests:

    ```bash
    kubectl apply -f deploy/manifests/web/
    ```

    ??? info "INFO"

        ??? question "Why?"

            one `apply` creates all three web objects: the Deployment (nginx
            pods), the ClusterIP Service (`web`, port 80), and a ConfigMap
            mounting `nginx.conf` — config lives outside the image so it can
            change without a rebuild (that's step 3.2's whole lesson).

        ??? info "Expected output"

            ```bash
            configmap/nginx-conf created
            deployment.apps/web created             # (1)!
            service/web created
            ```

            1.  Three kinds again — ConfigMap, Deployment, Service.

    The `nginx.conf` block that makes the proxy work:

    ```nginx
    location /api/ {
        proxy_pass http://app.tutorial.svc.cluster.local:8000;   # (1)
    }
    ```

    1.  `/api/*` requests are forwarded to the app Service by its DNS name —
        the full FQDN form from step 1.4, since `web` and `app` share the
        `tutorial` namespace.

3.  Bridge the web service to localhost:

    ```bash
    kubectl port-forward svc/web 8080:80
    ```

    ??? info "INFO"

        ??? question "Why?"

            the last hop for local browsing — `localhost:8080` → Service
            `web:80` → nginx pod. (Ingress replaces this in Phase 4.)

        ??? info "Expected output"

            ```bash
            Forwarding from 127.0.0.1:8080 -> 80      # (1)!
            ```

            1.  Keep this process running while you browse — Ctrl+C when
                done, or run it with `&` to background it.

!!! success "Verify"
    Browser → `localhost:8080` — UI loads and the progress list (served by
    web → app → postgres) renders. **All three tiers now live.**

---

## 3.2 — Config rollout without rebuild

**Goals:** Learn ConfigMap update semantics.

**Concepts:** Mounted ConfigMap volumes update, but apps don't hot-reload;
`rollout restart`; checksum annotations (revisited in
[Phase 5](phase-5.md)).

Edit `static/nginx.conf` first (change something visible, e.g. a header or
rate limit), then:

1.  Push the new ConfigMap:

    ```bash
    kubectl apply -f deploy/manifests/web/nginx-conf.yaml
    ```

    ??? info "INFO"

        ??? question "Why?"

            the ConfigMap manifest is generated from `static/nginx.conf` —
            `apply` updates the stored object in place. The kubelet syncs
            mounted ConfigMap volumes on a delay… but nginx never re-reads
            the file on its own.

        ??? info "Expected output"

            ```bash
            configmap/nginx-conf configured         # (1)!
            ```

            1.  `configured` = updated in place — yet the running pods still
                serve the *old* config.

2.  Restart the web pods to pick it up:

    ```bash
    kubectl rollout restart deploy/web
    ```

    ??? info "INFO"

        ??? question "Why?"

            mounted ConfigMaps refresh lazily and nginx doesn't watch the
            file — restart recreates pods which mount the *new* ConfigMap.
            (In Phase 5 this manual step is automated with a checksum
            annotation that forces a rollout whenever the config changes.)

        ??? info "Expected output"

            ```bash
            deployment.apps/web restarted           # (1)!
            ```

            1.  New pod(s) come up on the updated ConfigMap; old ones
                terminate (rolling, no downtime with 2+ replicas).

3.  Confirm the rollout completed:

    ```bash
    kubectl rollout status deploy/web
    ```

    ??? info "INFO"

        ??? info "Expected output"

            ```bash
            deployment "web" successfully rolled out
            ```

!!! success "Verify"
    New config active after restart; understand why restart was needed.
