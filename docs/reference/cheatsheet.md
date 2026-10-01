# Command cheat sheet

```bash
# Orientation
kubectl get <resource> -o wide|yaml|json
kubectl explain <resource>.<field>
kubectl api-resources | grep <x>

# Lifecycle
kubectl apply -f <file|dir>
kubectl delete -f <file>
kubectl rollout status|history|undo|restart deploy/<name>

# Debugging
kubectl describe pod <p>
kubectl logs <p> [-c container] [--previous] [-f]
kubectl exec -it <p> -- <cmd>
kubectl port-forward svc/<s> <local>:<remote>
kubectl debug -it <p> --image=<img> --target=<container>

# Throwaway pod — spin up, run a command, auto-delete on exit
kubectl run <name> --image=<img> --rm -it --restart=Never -- <cmd>
kubectl run randomstuff --image=busybox:1.36 --rm -it --restart=Never -- env
#   --rm = delete pod on exit · -it = interactive tty ·
#   --restart=Never = run once (required for one-shot cmds) · -- separates the pod's command

# Auth & security
kubectl auth can-i <verb> <resource> --as=<identity>
kubectl create secret generic|tls ...
kubectl create serviceaccount|role|rolebinding ...

# Helm
helm install|upgrade|rollback|uninstall <release> <chart>
helm template|lint|status|history|get values|get manifest
helm dependency update
helm repo add|update|search
```
