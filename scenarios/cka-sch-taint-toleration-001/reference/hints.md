# Hints
1. `kubectl describe pod` explains why they stay Pending; `kubectl describe node` shows the taint.
2. A taint is overcome by a toleration in the pod spec. Which key, value and effect does the taint have?
3. Patch `spec.template.spec.tolerations` with key `dedicated`, value `{{team}}`, effect `NoSchedule` and keep the existing nodeSelector.
