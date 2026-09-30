# Phase 3 — Web Tier (nginx)

## 3.1 — nginx deployment

**Goals:** Serve the tutorial UI; reverse-proxy API calls to the app tier.

**Concepts:** ConfigMap-mounted config, reverse proxy, multi-tier request flow.

```bash
nerdctl --namespace k8s.io build -t k8s-tutorial-web:0.1.0 ./static
kubectl apply -f deploy/manifests/web/   # deployment + service + nginx-conf ConfigMap
kubectl port-forward svc/web 8080:80
```

`static/nginx.conf` key block:

```nginx
location /api/ {
    proxy_pass http://app.tutorial.svc.cluster.local:8000;
}
```

!!! success "Verify"
    Browser → `localhost:8080` — UI loads and the progress list (served by
    web → app → postgres) renders. **All three tiers now live.**

---

## 3.2 — Config rollout without rebuild

**Goals:** Learn ConfigMap update semantics.

**Concepts:** Mounted ConfigMap volumes update, but apps don't hot-reload;
`rollout restart`; checksum annotations (revisited in
[Phase 5](phase-5.md)).

```bash
# edit static/nginx.conf, then:
kubectl apply -f deploy/manifests/web/nginx-conf.yaml
kubectl rollout restart deploy/web
kubectl rollout status deploy/web
```

!!! success "Verify"
    New config active after restart; understand why restart was needed.
