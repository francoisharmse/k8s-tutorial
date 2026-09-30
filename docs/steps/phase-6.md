# Phase 6 — Security

## Step 18 — Secrets encryption at rest

**Goals:** Understand why base64 Secrets aren't secure; enable etcd encryption.

**Concepts:** Secrets = base64 in etcd, EncryptionConfiguration (aescbc/KMS),
k3s `--secrets-encryption`, secret management strategy (SOPS, External Secrets).

```bash
kubectl get secret postgres-creds -o yaml     # readable → demonstrate the problem

# k3s / Rancher Desktop: enable via Preferences → Kubernetes, or k3s config:
#   /etc/rancher/k3s/config.yaml → secrets-encryption: true
# Full cluster: EncryptionConfiguration with aescbc provider.
# Verify encryption in etcd (control-plane host):
#   etcdctl get /registry/secrets/tutorial/postgres-creds | hexdump -C  → ciphertext
```

**Also cover:** why Secrets still shouldn't be committed to git →
`helm-secrets`/SOPS, or External Secrets Operator for production.

!!! success "Verify"
    Secret reads fine via API, but is ciphertext in etcd.

---

## Step 19 — RBAC

**Goals:** Give workloads and humans exactly the access they need — no more.

**Concepts:** ServiceAccounts, Role vs ClusterRole,
RoleBinding/ClusterRoleBinding, `kubectl auth can-i`, automounted tokens.

```bash
kubectl create serviceaccount app-sa -n tutorial
kubectl create role app-reader --verb=get,list --resource=configmaps -n tutorial
kubectl create rolebinding app-rb --role=app-reader \
  --serviceaccount=tutorial:app-sa -n tutorial

kubectl auth can-i get configmaps --as=system:serviceaccount:tutorial:app-sa    # yes
kubectl auth can-i create secrets --as=system:serviceaccount:tutorial:app-sa    # no
kubectl auth can-i --list --as=system:serviceaccount:tutorial:app-sa            # everything it can do

# wire the SA into the app deployment:  serviceAccountName: app-sa
# inspect the mounted token inside the pod:
kubectl exec -it deploy/app -- ls /var/run/secrets/kubernetes.io/serviceaccount
kubectl exec -it deploy/app -- cat /var/run/secrets/kubernetes.io/serviceaccount/token | cut -d. -f2 | base64 -d
```

!!! tip "Bonus"
    Create a `viewer` SA with `get,list,watch` on everything in `tutorial` —
    a read-only "junior SRE" account.

!!! success "Verify"
    `auth can-i` confirms allow/deny exactly as intended.

---

## Step 20 — Pod security & securityContext

**Goals:** Harden containers; enforce standards at the namespace level.

**Concepts:** Pod Security Standards (privileged/baseline/restricted), Pod
Security Admission labels, `securityContext` fields.

```bash
kubectl label namespace tutorial pod-security.kubernetes.io/enforce=baseline

# then harden each container:
#   securityContext:
#     runAsNonRoot: true
#     readOnlyRootFilesystem: true
#     allowPrivilegeEscalation: false
#     capabilities: { drop: [ALL] }

# try enforce=restricted before hardening → watch pods get REJECTED:
kubectl get events --field-selector reason=FailedCreate
kubectl apply -f ...   # admission error is explicit about which field violates
```

!!! success "Verify"
    With `restricted` enforcement, hardened pods run and unhardened ones are
    rejected with clear admission errors.

---

## Step 21 — NetworkPolicies

**Goals:** Enforce tier-to-tier traffic rules at the network level.

**Concepts:** default-deny + explicit allow, pod selectors, ingress/egress
rules. (k3s's built-in controller enforces these; not all CNIs do.)

```yaml
# deploy/manifests/netpol/: default-deny-ingress for the namespace, then allow:
#   ingress-controller → web:80
#   web → app:8000
#   app → pg-postgresql:5432
#   (+ egress to kube-dns or nothing resolves)
```

```bash
kubectl apply -f deploy/manifests/netpol/
kubectl get networkpolicy
# Test the matrix:
kubectl exec -it deploy/web -- curl -m3 http://app:8000/healthz    # allowed
kubectl exec -it deploy/app -- curl -m3 http://web:80              # denied (times out)
kubectl exec -it deploy/web -- curl -m3 pg-postgresql:5432         # denied
```

!!! success "Verify"
    Exactly the allowed paths work; everything else times out. Sketch the
    resulting flow: ingress → web → app → db, nothing else.
