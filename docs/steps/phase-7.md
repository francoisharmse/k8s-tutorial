# Phase 7 — Operations at Scale

## 7.1 — Scaling, rolling updates, rollbacks, PDBs

**Goals:** Change running workloads safely; protect availability during
disruption.

**Concepts:** replicas, rolling update (`maxSurge`/`maxUnavailable`), rollout
history, PodDisruptionBudget, cordon/drain.

```bash
kubectl scale deploy/app --replicas=3
kubectl set image deploy/app app=k8s-tutorial-app:0.2.0   # or: helm upgrade --set
kubectl rollout status deploy/app
kubectl rollout history deploy/app
kubectl rollout undo deploy/app                          # instant rollback

kubectl apply -f deploy/manifests/app/pdb.yaml           # minAvailable: 1
kubectl cordon <node>
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
kubectl uncordon <node>
```

!!! success "Verify"
    During the rolling update, `kubectl get pods -w` shows old pods terminating
    only after new ones are Ready — zero downtime.

---

## 7.2 — Horizontal Pod Autoscaler

**Goals:** Scale on real load.

**Concepts:** HPA, metrics-server dependency, scale-up/down stabilization
windows.

```bash
kubectl autoscale deploy/app --min=2 --max=6 --cpu-percent=70
kubectl get hpa -w

# generate load:
kubectl run loadgen --image=busybox:1.36 --rm -it --restart=Never -- \
  /bin/sh -c 'while true; do wget -q -O- http://app:8000/api/steps > /dev/null; done'
# watch replicas climb → Ctrl+C → watch scale-down after cooldown
```

!!! success "Verify"
    HPA scales app under load and scales back down. Requires resource
    `requests` — HPA percentages are relative to them.

---

## 7.3 — Logging & debugging toolkit

**Goals:** Build the real-world debugging muscle.

**Concepts:** Log sources/rotation, events vs logs, ephemeral debug containers,
multi-pod tailing.

```bash
kubectl logs deploy/app -f --tail=50 --since=10m
kubectl logs -l tier=app --all-containers --prefix
stern app -n tutorial                                  # multi-pod tail (brew install stern)
kubectl get events -n tutorial --sort-by=.lastTimestamp -w

kubectl debug -it <pod> --image=busybox:1.36 --target=app    # ephemeral container
kubectl run netshoot --rm -it --image=nicolaka/netshoot      # the swiss army knife
```

!!! success "Verify"
    Given a broken pod, you can triage: `describe` → `logs --previous` →
    `debug`/`netshoot`.

---

## 7.4 — Jobs & database backup/restore

**Goals:** Run one-off and scheduled work; prove backups actually restore.

**Concepts:** Job vs CronJob, completions/backoff, `pg_dump`, backup PVC,
initContainers.

```bash
# CronJob: nightly pg_dump → dedicated PVC
kubectl apply -f deploy/manifests/db/backup-cronjob.yaml
kubectl get cronjob

# trigger a manual run without waiting for the schedule:
kubectl create job manual-backup-1 --from=cronjob/db-backup
kubectl logs job/manual-backup-1

# restore drill: load the dump into a scratch database — a backup
# you've never restored is just a hope, not a backup
kubectl exec -it pg-postgresql-0 -- psql -U postgres -c 'CREATE DATABASE restore_test'
kubectl exec -i pg-postgresql-0 -- psql -U postgres -d restore_test < dump.sql
```

!!! success "Verify"
    `restore_test` contains the `progress` table and its rows.
