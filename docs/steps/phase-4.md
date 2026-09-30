# Phase 4 — Ingress & TLS

## 4.1 — Ingress (Traefik, built into k3s)

**Goals:** Route external traffic by hostname/path instead of port-forward.

**Concepts:** Ingress resource vs ingress controller, host/path routing,
`/etc/hosts`.

```bash
kubectl get pods -n kube-system | grep traefik     # the controller k3s ships

# add to /etc/hosts:   127.0.0.1  k8s-tutorial.local
kubectl apply -f deploy/manifests/ingress/         # host k8s-tutorial.local → svc/web:80
kubectl get ingress tutorial
kubectl describe ingress tutorial
```

!!! success "Verify"
    `http://k8s-tutorial.local` loads the app — no port-forward.

!!! note "Rancher Manager downstream cluster"
    The controller may be nginx rather than Traefik, and the external IP comes
    from a LoadBalancer instead of localhost.

---

## 4.2 — TLS

**Goals:** Serve HTTPS; manage certs as cluster objects.

**Concepts:** TLS secret type, cert termination at ingress.

```bash
mkcert k8s-tutorial.local          # or: openssl req -x509 ...
kubectl create secret tls tutorial-tls \
  --cert=k8s-tutorial.local.pem --key=k8s-tutorial.local-key.pem
kubectl get secret tutorial-tls -o yaml        # note type: kubernetes.io/tls
# add tls: section to ingress.yaml, re-apply
```

!!! success "Verify"
    `https://k8s-tutorial.local` with a trusted cert (mkcert) or browser warning
    (self-signed openssl).
