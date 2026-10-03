# Which container fails, and how

## Approach
`kubectl get pods` shows `2/3` Ready; `kubectl describe pod` lists each container's state. The failing one has `Last State: Terminated (Reason: Error, Exit Code: {{code}})`.
`kubectl logs deployment/{{app}} -c {{bad}} --previous` shows the error line. Record the answer with `kubectl create configmap {{app}}-findings --from-literal=container={{bad}} --from-literal=exitCode={{code}}`.

## What the verifier checks
The ConfigMap's `container` equals `{{bad}}` and `exitCode` equals `{{code}}`; the Deployment spec and UID are unchanged.

## Why shortcuts fail
Guessing the main container gives the wrong name; modifying the pod violates the diagnose-only guard.
