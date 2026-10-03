# KOPS scenario backlog and coverage

Owner: scenario authoring track. Generated state as of 2026-10-02 from `scenarios/*`, the selftest logs of this authoring session and the design entries below.
Per-profile reporting only: CKA and CKAD are never combined.

## 1. Summary

| Item | Count |
|---|---|
| Scenarios implemented (directories under `scenarios/`) | 60 |
| of which `status: validated` (lint clean and `kops selftest` PASSED) | 60 |
| of which `status: draft` | 0 |
| Backlog designs (section 4) | 40 |
| CKA competencies with a validated primary scenario | 22 of 27 |
| CKA competencies with a backlog design only | 5 |
| CKA competencies with a draft scenario only | 0 |
| CKA competencies uncovered (no scenario, no design) | 0 |
| CKAD competencies with a validated primary scenario | 21 of 24 |
| CKAD competencies with a backlog design only | 3 |
| CKAD competencies with a draft scenario only | 0 |
| CKAD competencies uncovered (no scenario, no design) | 0 |
| Validated scenarios by difficulty (1 / 2 / 3) | 3 / 47 / 10 |
| Validated scenarios that are spec-only (no behavioural proof) | 3 |
| Scenarios needing extra worker nodes (`topology.workers` > 0) | 7 |

## 2. Implemented scenarios

Selftest = null agent FAILs, every `reference/wrong-*.sh` FAILs, `reference/solution.sh` replayed 3 times PASSes, every cluster destroyed (`clean_reset`). Seed 1.

| id | status | CKA | CKAD | family | diff | key skills | selftest |
|---|---|---|---|---|---|---|---|
| `cka-arc-extension-interfaces-report-001` | validated | CKA-ARC-07 | - | PF-EXT-003 | 2 | cri, cni, csi, extension-interfaces, diagnosis | PASS (null, 0 wrong-fix, 3x oracle) 1m22s |
| `cka-net-coredns-two-layer-repair-001` | validated | CKA-NET-06 | - | PF-NET-009 | 3 | coredns, dns, corefile, kube-system | PASS (null, 2 wrong-fix, 3x oracle) 4m53s |
| `cka-net-headless-statefulset-dns-001` | validated | CKA-NET-03 | CKAD-SNW-02 | PF-NET-002 | 2 | statefulset, headless-service, dns, service | PASS (null, 2 wrong-fix, 3x oracle) 3m50s |
| `cka-net-kubeproxy-rollout-undo-001` | validated | CKA-TRB-02 | - | PF-NET-011 | 3 | kube-proxy, daemonset, rollout, clusterip, troubleshooting | PASS (null, 2 wrong-fix, 3x oracle) 5m44s |
| `cka-sch-drain-maintenance-node-001` | validated | CKA-ARC-04 | - | PF-SCH-006 | 2 | drain, cordon, maintenance, daemonset, emptydir | PASS (null, 2 wrong-fix, 3x oracle) 5m00s |
| `cka-sch-nodeselector-pending-001` | validated | CKA-WLS-05 | - | PF-SCH-005 | 2 | scheduling, nodeselector, pending, labels | PASS (null, 2 wrong-fix, 3x oracle) 4m45s |
| `cka-sch-priorityclass-001` | validated | CKA-WLS-05 | - | PF-SCH-004 | 1 | priorityclass, scheduling, create | PASS (null, 2 wrong-fix, 3x oracle) 3m00s |
| `cka-sch-taint-toleration-001` | validated | CKA-WLS-05 | - | PF-SCH-002 | 2 | scheduling, taints, tolerations, nodeselector | PASS (null, 2 wrong-fix, 3x oracle) 3m47s |
| `cka-sch-topology-spread-001` | validated | CKA-WLS-05 | - | PF-SCH-003 | 2 | scheduling, topologyspreadconstraints, nodeselector | PASS (null, 2 wrong-fix, 3x oracle) 4m27s |
| `cka-sec-clusterrole-nodes-001` | validated | CKA-ARC-01 | - | PF-SEC-002 | 2 | rbac, clusterrole, clusterrolebinding, nodes | PASS (null, 2 wrong-fix, 3x oracle) 2m05s |
| `cka-sto-default-class-001` | validated | CKA-STO-01 | - | PF-STO-001 | 2 | storageclass, default-class, annotations | PASS (null, 2 wrong-fix, 3x oracle) 2m37s |
| `cka-sto-pv-bind-repair-001` | validated | CKA-STO-03 | - | PF-STO-002 | 3 | pv, pvc, binding, storageclass, accessmodes | PASS (null, 2 wrong-fix, 3x oracle) 4m58s |
| `cka-sto-reclaim-retain-001` | validated | CKA-STO-02 | - | PF-STO-003 | 2 | pv, reclaim-policy, retain, pvc | PASS (null, 2 wrong-fix, 3x oracle) 2m35s |
| `cka-trb-node-capacity-diagnose-001` | validated | CKA-TRB-03 | - | PF-OBS-006 | 3 | diagnosis, resource-usage, describe-node, requests | PASS (null, 2 wrong-fix, 3x oracle) 2m44s |
| `cka-trb-node-unschedulable-001` | validated | CKA-TRB-01 | - | PF-NOD-005 | 2 | nodes, cordon, taints, pending, capacity | PASS (null, 2 wrong-fix, 3x oracle) 4m30s |
| `cka-wl-daemonset-controlplane-001` | validated | CKA-WLS-04 | - | PF-WKL-007 | 2 | daemonset, tolerations, control-plane | PASS (null, 1 wrong-fix, 3x oracle) 3m28s |
| `cka-wl-hpa-spec-001` | validated | CKA-WLS-03 | - | PF-WKL-011 | 2 | hpa, autoscaling, requests, spec-only | PASS (null, 2 wrong-fix, 3x oracle) 2m05s |
| `cka-wl-pdb-protect-001` | validated | CKA-WLS-04 | - | PF-WKL-012 | 1 | pdb, availability, labels | PASS (null, 2 wrong-fix, 3x oracle) 3m59s |
| `ckad-cfg-downward-volume-001` | validated | - | CKAD-ADB-04 | PF-CFG-003 | 2 | downward-api, volumes, labels | PASS (null, 2 wrong-fix, 3x oracle) 4m08s |
| `ckad-cfg-projected-volume-001` | validated | - | CKAD-ADB-04 | PF-CFG-003 | 2 | projected-volume, configmap, secret, volumes | PASS (null, 2 wrong-fix, 3x oracle) 4m07s |
| `ckad-deploy-bluegreen-cutover-001` | validated | - | CKAD-ADP-01 | PF-WKL-004 | 2 | blue-green, deployment-strategy, service-selector | PASS (null, 2 wrong-fix, 3x oracle) 3m20s |
| `ckad-deploy-canary-share-001` | validated | - | CKAD-ADP-01 | PF-WKL-004 | 2 | canary, deployment-strategy, service-selector, labels | PASS (null, 3 wrong-fix, 3x oracle) 5m25s |
| `ckad-obs-api-deprecation-001` | validated | - | CKAD-AOM-01 | PF-OBS-005 | 2 | api-deprecation, api-versions, configmap, spec-only | PASS (null, 2 wrong-fix, 3x oracle) 2m01s |
| `ckad-obs-cli-report-001` | validated | - | CKAD-AOM-03 | PF-OBS-006 | 2 | kubectl, jsonpath, sort-by, custom-columns, diagnosis | PASS (null, 2 wrong-fix, 3x oracle) 2m44s |
| `ckad-sec-securitycontext-hardening-001` | validated | - | CKAD-AEC-08 | PF-SEC-005 | 3 | securitycontext, readonlyrootfilesystem, capabilities, emptydir | PASS (null, 2 wrong-fix, 3x oracle) 4m39s |
| `ckad-sec-serviceaccount-workload-001` | validated | - | CKAD-AEC-07 | PF-SEC-004 | 2 | serviceaccount, automount, deployment | PASS (null, 2 wrong-fix, 3x oracle) 4m14s |
| `kops-cfg-configmap-ref-repair-001` | validated | CKA-WLS-02 | CKAD-AEC-05 | PF-CFG-001 | 2 | configmap, env, createcontainerconfigerror | PASS (null, 2 wrong-fix, 3x oracle) 3m46s |
| `kops-cfg-secret-env-001` | validated | CKA-WLS-02 | CKAD-AEC-06 | PF-CFG-002 | 2 | secret, env, create | PASS (null, 2 wrong-fix, 3x oracle) 3m25s |
| `kops-cfg-subpath-refresh-001` | validated | CKA-WLS-02 | CKAD-AEC-05 | PF-CFG-001 | 2 | configmap, volume, subpath, rollout-restart | PASS (null, 2 wrong-fix, 3x oracle) 4m10s |
| `kops-ext-crd-discover-001` | validated | CKA-ARC-08 | CKAD-AEC-01 | PF-EXT-001 | 2 | crd, custom-resources, discovery, api-resources | PASS (null, 2 wrong-fix, 3x oracle) 2m08s |
| `kops-job-cronjob-create-001` | validated | CKA-WLS-04 | CKAD-ADB-02 | PF-WKL-006 | 2 | cronjob, job, schedule, concurrencypolicy, create | PASS (null, 2 wrong-fix, 3x oracle) 3m08s |
| `kops-job-cronjob-repair-001` | validated | CKA-WLS-04 | CKAD-ADB-02 | PF-WKL-006 | 2 | cronjob, job, image, create-job-from | PASS (null, 2 wrong-fix, 3x oracle) 3m07s |
| `kops-job-native-sidecar-001` | validated | CKA-WLS-04 | CKAD-ADB-03 | PF-WKL-008 | 3 | sidecar, native-sidecar, cronjob, job, initcontainers | PASS (null, 2 wrong-fix, 3x oracle) 4m22s |
| `kops-mc-sidecar-log-stream-001` | validated | CKA-WLS-04 | CKAD-ADB-03 | PF-WKL-008 | 2 | sidecar, multi-container, emptydir, logs | PASS (null, 1 wrong-fix, 3x oracle) 4m07s |
| `kops-net-cross-namespace-dns-001` | validated | CKA-NET-06 | CKAD-SNW-02 | PF-NET-010 | 2 | dns, service-discovery, logs, cross-namespace | PASS (null, 2 wrong-fix, 3x oracle) 5m02s |
| `kops-net-externalname-alias-001` | validated | CKA-NET-03 | CKAD-SNW-02 | PF-NET-002 | 1 | service, externalname, dns, cross-namespace | PASS (null, 2 wrong-fix, 3x oracle) 3m53s |
| `kops-net-hostnetwork-dns-001` | validated | CKA-NET-01 | CKAD-SNW-02 | PF-NET-010 | 2 | hostnetwork, dnspolicy, dns, pod-networking, logs | PASS (null, 2 wrong-fix, 3x oracle) 4m41s |
| `kops-net-ingress-rules-001` | validated | CKA-NET-05 | CKAD-SNW-03 | PF-NET-007 | 2 | ingress, pathtype, ingressclass, spec-only | PASS (null, 2 wrong-fix, 3x oracle) 2m09s |
| `kops-net-multiport-service-repair-001` | validated | CKA-TRB-05 | CKAD-SNW-02 | PF-NET-003 | 2 | service, named-port, targetport, endpoints, multi-port | PASS (null, 2 wrong-fix, 3x oracle) 4m06s |
| `kops-net-netpol-cross-namespace-001` | validated | CKA-NET-02 | CKAD-SNW-01 | PF-NET-004 | 3 | networkpolicy, namespaceselector, cross-namespace | PASS (null, 3 wrong-fix, 3x oracle) 4m52s |
| `kops-net-netpol-egress-dns-001` | validated | CKA-NET-02 | CKAD-SNW-01 | PF-NET-005 | 2 | networkpolicy, egress, dns | PASS (null, 2 wrong-fix, 3x oracle) 9m29s |
| `kops-net-netpol-ingress-repair-001` | validated | CKA-TRB-05 | CKAD-SNW-01 | PF-NET-006 | 2 | networkpolicy, ingress, labels, ports | PASS (null, 3 wrong-fix, 3x oracle) 5m39s |
| `kops-net-nodeport-expose-001` | validated | CKA-NET-03 | CKAD-SNW-02 | PF-NET-001 | 2 | service, nodeport, expose | PASS (null, 2 wrong-fix, 3x oracle) 2m52s |
| `kops-net-service-endpoint-repair-001` | validated | CKA-TRB-05 | CKAD-SNW-02 | PF-NET-003 | 2 | service, endpoints, selector, targetport | PASS (null, 2 wrong-fix, 3x oracle) 3m29s |
| `kops-obs-logs-env-diagnose-001` | validated | CKA-TRB-04 | CKAD-AOM-04 | PF-OBS-002 | 2 | logs, crashloopbackoff, env, troubleshooting | PASS (null, 2 wrong-fix, 3x oracle) 4m28s |
| `kops-obs-multicontainer-findings-001` | validated | CKA-TRB-04 | CKAD-AOM-05 | PF-OBS-004 | 2 | diagnosis, multi-container, exit-code, logs | PASS (null, 2 wrong-fix, 3x oracle) 2m34s |
| `kops-obs-probe-repair-001` | validated | CKA-WLS-04 | CKAD-AOM-02 | PF-OBS-001 | 2 | probes, readiness, liveness, endpoints | PASS (null, 2 wrong-fix, 3x oracle) 7m07s |
| `kops-obs-probe-startup-001` | validated | CKA-WLS-04 | CKAD-AOM-02 | PF-OBS-001 | 2 | probes, liveness, startupprobe, crashloop | PASS (null, 2 wrong-fix, 3x oracle) 8m29s |
| `kops-res-limitrange-max-001` | validated | CKA-WLS-05 | CKAD-AEC-03 | PF-CFG-005 | 2 | limitrange, resources, admission, limits | PASS (null, 2 wrong-fix, 3x oracle) 3m16s |
| `kops-res-oomkilled-limit-001` | validated | CKA-WLS-05 | CKAD-AEC-04 | PF-CFG-004 | 2 | resources, limits, oomkilled | PASS (null, 2 wrong-fix, 3x oracle) 3m56s |
| `kops-sec-pss-restricted-001` | validated | CKA-WLS-05 | CKAD-AEC-02 | PF-SEC-006 | 2 | pod-security, admission, restricted | PASS (null, 2 wrong-fix, 3x oracle) 3m49s |
| `kops-sec-rbac-forbidden-repair-001` | validated | CKA-ARC-01 | CKAD-AEC-02 | PF-SEC-003 | 3 | rbac, forbidden, troubleshooting, apigroup | PASS (null, 2 wrong-fix, 3x oracle) 2m04s |
| `kops-sec-rbac-namespaced-001` | validated | CKA-ARC-01 | CKAD-AEC-02 | PF-SEC-001 | 2 | rbac, role, rolebinding, serviceaccount, least-privilege | PASS (null, 2 wrong-fix, 3x oracle) 2m05s |
| `kops-sto-pvc-reference-repair-001` | validated | CKA-STO-03 | CKAD-ADB-04 | PF-STO-002 | 2 | pvc, volume, pending, persistence | PASS (null, 2 wrong-fix, 3x oracle) 5m12s |
| `kops-trb-init-dependency-001` | validated | CKA-WLS-04 | CKAD-ADB-03 | PF-WKL-009 | 2 | init-containers, service, dependencies, logs | PASS (null, 2 wrong-fix, 3x oracle) 4m37s |
| `kops-trb-multi-workload-triage-001` | validated | CKA-TRB-04 | CKAD-AOM-05 | PF-OBS-004 | 3 | troubleshooting, imagepullbackoff, crashloopbackoff, pending, multi-fault | PASS (null, 2 wrong-fix, 3x oracle) 5m46s |
| `kops-trb-startup-cascade-001` | validated | CKA-TRB-05 | CKAD-AOM-05 | PF-OBS-004 | 3 | troubleshooting, serviceaccount, configmap, volume, service | PASS (null, 2 wrong-fix, 3x oracle) 4m29s |
| `kops-wl-recreate-strategy-001` | validated | CKA-WLS-01 | CKAD-ADP-02 | PF-WKL-002 | 2 | deployment, strategy, recreate | PASS (null, 2 wrong-fix, 3x oracle) 4m15s |
| `kops-wl-rollout-pause-batch-001` | validated | CKA-WLS-01 | CKAD-ADP-02 | PF-WKL-002 | 2 | deployment, rollout, pause, resume, revision | PASS (null, 2 wrong-fix, 3x oracle) 4m08s |
| `kops-wl-rollout-undo-to-revision-001` | validated | CKA-WLS-01 | CKAD-ADP-02 | PF-WKL-003 | 2 | deployment, rollout, rollback, history | PASS (null, 2 wrong-fix, 3x oracle) 4m35s |

## 3. Coverage matrix

Legend: **implemented** = at least one validated scenario with this primary competency; **draft** = only draft scenarios; **backlog** = a design exists in section 4 but the current backend cannot run it; **uncovered** = neither. Secondary competencies are never counted.

### CKA (curriculum v1.35)

| Domain (weight) | Competency | State | Validated scenarios | Backlog designs |
|---|---|---|---|---|
| Storage (10%) | CKA-STO-01 Implement storage classes and dynamic volume provisioning | **implemented** | `cka-sto-default-class-001` | `kops-sto-pvc-create-mount-001`, `kops-sto-pvc-expand-001` |
| Storage (10%) | CKA-STO-02 Configure volume types, access modes and reclaim policies | **implemented** | `cka-sto-reclaim-retain-001` | - |
| Storage (10%) | CKA-STO-03 Manage persistent volumes and persistent volume claims | **implemented** | `cka-sto-pv-bind-repair-001`, `kops-sto-pvc-reference-repair-001` | - |
| Troubleshooting (30%) | CKA-TRB-01 Troubleshoot clusters and nodes | **implemented** | `cka-trb-node-unschedulable-001` | `cka-trb-kubelet-stopped-001`, `cka-trb-kubelet-config-path-001`, `cka-trb-containerd-stopped-001`, `cka-trb-node-loss-recovery-001`, `cka-trb-node-pressure-evict-001` |
| Troubleshooting (30%) | CKA-TRB-02 Troubleshoot cluster components | **implemented** | `cka-net-kubeproxy-rollout-undo-001` | `cka-trb-apiserver-flag-001`, `cka-trb-scheduler-manifest-001`, `cka-trb-controller-manager-001`, `cka-net-cni-conf-removed-001` |
| Troubleshooting (30%) | CKA-TRB-03 Monitor cluster and application resource usage | **implemented** | `cka-trb-node-capacity-diagnose-001` | `cka-trb-resource-usage-top-001` |
| Troubleshooting (30%) | CKA-TRB-04 Manage and evaluate container output streams | **implemented** | `kops-obs-logs-env-diagnose-001`, `kops-obs-multicontainer-findings-001`, `kops-trb-multi-workload-triage-001` | - |
| Troubleshooting (30%) | CKA-TRB-05 Troubleshoot services and networking | **implemented** | `kops-net-multiport-service-repair-001`, `kops-net-netpol-ingress-repair-001`, `kops-net-service-endpoint-repair-001`, `kops-trb-startup-cascade-001` | `kops-multi-context-fix-001` |
| Workloads and Scheduling (15%) | CKA-WLS-01 Understand application deployments and how to perform rolling update and rollbacks | **implemented** | `kops-wl-recreate-strategy-001`, `kops-wl-rollout-pause-batch-001`, `kops-wl-rollout-undo-to-revision-001` | - |
| Workloads and Scheduling (15%) | CKA-WLS-02 Use ConfigMaps and Secrets to configure applications | **implemented** | `kops-cfg-configmap-ref-repair-001`, `kops-cfg-secret-env-001`, `kops-cfg-subpath-refresh-001` | - |
| Workloads and Scheduling (15%) | CKA-WLS-03 Configure workload autoscaling | **implemented** | `cka-wl-hpa-spec-001` | `cka-wl-hpa-scale-under-load-001` |
| Workloads and Scheduling (15%) | CKA-WLS-04 Understand the primitives used to create robust, self-healing, application deployments | **implemented** | `cka-wl-daemonset-controlplane-001`, `cka-wl-pdb-protect-001`, `kops-job-cronjob-create-001`, `kops-job-cronjob-repair-001`, `kops-job-native-sidecar-001`, `kops-mc-sidecar-log-stream-001`, `kops-obs-probe-repair-001`, `kops-obs-probe-startup-001`, `kops-trb-init-dependency-001` | `kops-wl-statefulset-create-001`, `kops-wl-job-parallel-completions-001`, `cka-sch-static-pod-001` |
| Workloads and Scheduling (15%) | CKA-WLS-05 Configure Pod admission and scheduling (limits, node affinity, etc.) | **implemented** | `cka-sch-nodeselector-pending-001`, `cka-sch-priorityclass-001`, `cka-sch-taint-toleration-001`, `cka-sch-topology-spread-001`, `kops-res-limitrange-max-001`, `kops-res-oomkilled-limit-001`, `kops-sec-pss-restricted-001` | - |
| Cluster Architecture, Installation and Configuration (25%) | CKA-ARC-01 Manage role based access control (RBAC) | **implemented** | `cka-sec-clusterrole-nodes-001`, `kops-sec-rbac-forbidden-repair-001`, `kops-sec-rbac-namespaced-001` | `cka-arc-user-csr-rbac-001`, `cka-sec-audit-who-deleted-001` |
| Cluster Architecture, Installation and Configuration (25%) | CKA-ARC-02 Prepare underlying infrastructure for installing a Kubernetes cluster | **backlog** | - | `cka-arc-node-prep-sysctl-001` |
| Cluster Architecture, Installation and Configuration (25%) | CKA-ARC-03 Create and manage Kubernetes clusters using kubeadm | **backlog** | - | `cka-arc-apiserver-admission-plugin-001`, `cka-arc-kubeadm-join-worker-001` |
| Cluster Architecture, Installation and Configuration (25%) | CKA-ARC-04 Manage the lifecycle of Kubernetes clusters | **implemented** | `cka-sch-drain-maintenance-node-001` | `cka-arc-etcd-snapshot-001`, `cka-arc-etcd-restore-001`, `cka-arc-cert-expiry-inspect-001`, `cka-arc-cert-renew-apiserver-001`, `cka-arc-kubeadm-upgrade-001` |
| Cluster Architecture, Installation and Configuration (25%) | CKA-ARC-05 Implement and configure a highly-available control plane | **backlog** | - | `cka-arc-ha-add-controlplane-001` |
| Cluster Architecture, Installation and Configuration (25%) | CKA-ARC-06 Use Helm and Kustomize to install cluster components | **backlog** | - | `cka-arc-helm-install-values-001`, `cka-arc-helm-release-repair-001`, `cka-arc-kustomize-overlay-001` |
| Cluster Architecture, Installation and Configuration (25%) | CKA-ARC-07 Understand extension interfaces (CNI, CSI, CRI, etc.) | **implemented** | `cka-arc-extension-interfaces-report-001` | `cka-arc-extension-interfaces-001` |
| Cluster Architecture, Installation and Configuration (25%) | CKA-ARC-08 Understand CRDs, install and configure operators | **implemented** | `kops-ext-crd-discover-001` | `cka-arc-operator-install-001` |
| Servicing and Networking (20%) | CKA-NET-01 Understand connectivity between Pods | **implemented** | `kops-net-hostnetwork-dns-001` | - |
| Servicing and Networking (20%) | CKA-NET-02 Define and enforce Network Policies | **implemented** | `kops-net-netpol-cross-namespace-001`, `kops-net-netpol-egress-dns-001` | `kops-net-netpol-create-001` |
| Servicing and Networking (20%) | CKA-NET-03 Use ClusterIP, NodePort, LoadBalancer service types and endpoints | **implemented** | `cka-net-headless-statefulset-dns-001`, `kops-net-externalname-alias-001`, `kops-net-nodeport-expose-001` | `kops-net-loadbalancer-001`, `cka-net-nodeport-from-node-001` |
| Servicing and Networking (20%) | CKA-NET-04 Use the Gateway API to manage Ingress traffic | **backlog** | - | `cka-net-gateway-api-httproute-001` |
| Servicing and Networking (20%) | CKA-NET-05 Know how to use Ingress controllers and Ingress resources | **implemented** | `kops-net-ingress-rules-001` | `cka-net-ingress-controller-routing-001` |
| Servicing and Networking (20%) | CKA-NET-06 Understand and use CoreDNS | **implemented** | `cka-net-coredns-two-layer-repair-001`, `kops-net-cross-namespace-dns-001` | `cka-net-coredns-stubdomain-001` |

Domain roll-up:

| Domain | Weight | Competencies | implemented | backlog only | uncovered | validated scenarios (primary) |
|---|---|---|---|---|---|---|
| Storage | 10% | 3 | 3 | 0 | 0 | 4 |
| Troubleshooting | 30% | 5 | 5 | 0 | 0 | 10 |
| Workloads and Scheduling | 15% | 5 | 5 | 0 | 0 | 23 |
| Cluster Architecture, Installation and Configuration | 25% | 8 | 4 | 4 | 0 | 6 |
| Servicing and Networking | 20% | 6 | 5 | 1 | 0 | 9 |

### CKAD (curriculum v1.35)

| Domain (weight) | Competency | State | Validated scenarios | Backlog designs |
|---|---|---|---|---|
| Application Design and Build (20%) | CKAD-ADB-01 Define, build and modify container images | **backlog** | - | `ckad-img-build-push-001` |
| Application Design and Build (20%) | CKAD-ADB-02 Choose and use the right workload resource (Deployment, DaemonSet, CronJob, etc.) | **implemented** | `kops-job-cronjob-create-001`, `kops-job-cronjob-repair-001` | `kops-wl-statefulset-create-001`, `kops-wl-job-parallel-completions-001` |
| Application Design and Build (20%) | CKAD-ADB-03 Understand multi-container Pod design patterns (e.g. sidecar, init and others) | **implemented** | `kops-job-native-sidecar-001`, `kops-mc-sidecar-log-stream-001`, `kops-trb-init-dependency-001` | - |
| Application Design and Build (20%) | CKAD-ADB-04 Utilize persistent and ephemeral volumes | **implemented** | `ckad-cfg-downward-volume-001`, `ckad-cfg-projected-volume-001`, `kops-sto-pvc-reference-repair-001` | `kops-sto-pvc-create-mount-001` |
| Application Deployment (20%) | CKAD-ADP-01 Use Kubernetes primitives to implement common deployment strategies (e.g. blue/green or canary) | **implemented** | `ckad-deploy-bluegreen-cutover-001`, `ckad-deploy-canary-share-001` | - |
| Application Deployment (20%) | CKAD-ADP-02 Understand Deployments and how to perform rolling updates | **implemented** | `kops-wl-recreate-strategy-001`, `kops-wl-rollout-pause-batch-001`, `kops-wl-rollout-undo-to-revision-001` | - |
| Application Deployment (20%) | CKAD-ADP-03 Use the Helm package manager to deploy existing packages | **backlog** | - | `cka-arc-helm-install-values-001`, `cka-arc-helm-release-repair-001` |
| Application Deployment (20%) | CKAD-ADP-04 Kustomize | **backlog** | - | `cka-arc-kustomize-overlay-001` |
| Application Observability and Maintenance (15%) | CKAD-AOM-01 Understand API depreciations | **implemented** | `ckad-obs-api-deprecation-001` | - |
| Application Observability and Maintenance (15%) | CKAD-AOM-02 Implement probes and health checks | **implemented** | `kops-obs-probe-repair-001`, `kops-obs-probe-startup-001` | - |
| Application Observability and Maintenance (15%) | CKAD-AOM-03 Use built-in CLI tools to monitor Kubernetes applications | **implemented** | `ckad-obs-cli-report-001` | `cka-trb-resource-usage-top-001` |
| Application Observability and Maintenance (15%) | CKAD-AOM-04 Utilize container logs | **implemented** | `kops-obs-logs-env-diagnose-001` | - |
| Application Observability and Maintenance (15%) | CKAD-AOM-05 Debugging in Kubernetes | **implemented** | `kops-obs-multicontainer-findings-001`, `kops-trb-multi-workload-triage-001`, `kops-trb-startup-cascade-001` | - |
| Application Environment, Configuration and Security (25%) | CKAD-AEC-01 Discover and use resources that extend Kubernetes (CRD, Operators) | **implemented** | `kops-ext-crd-discover-001` | `cka-arc-operator-install-001` |
| Application Environment, Configuration and Security (25%) | CKAD-AEC-02 Understand authentication, authorization and admission control | **implemented** | `kops-sec-pss-restricted-001`, `kops-sec-rbac-forbidden-repair-001`, `kops-sec-rbac-namespaced-001` | `cka-arc-user-csr-rbac-001`, `cka-sec-audit-who-deleted-001` |
| Application Environment, Configuration and Security (25%) | CKAD-AEC-03 Understand requests, limits, quotas | **implemented** | `kops-res-limitrange-max-001` | - |
| Application Environment, Configuration and Security (25%) | CKAD-AEC-04 Define resource requirements | **implemented** | `kops-res-oomkilled-limit-001` | - |
| Application Environment, Configuration and Security (25%) | CKAD-AEC-05 Understand ConfigMaps | **implemented** | `kops-cfg-configmap-ref-repair-001`, `kops-cfg-subpath-refresh-001` | - |
| Application Environment, Configuration and Security (25%) | CKAD-AEC-06 Create & consume Secrets | **implemented** | `kops-cfg-secret-env-001` | - |
| Application Environment, Configuration and Security (25%) | CKAD-AEC-07 Understand ServiceAccounts | **implemented** | `ckad-sec-serviceaccount-workload-001` | - |
| Application Environment, Configuration and Security (25%) | CKAD-AEC-08 Understand Application Security (SecurityContexts, Capabilities, etc.) | **implemented** | `ckad-sec-securitycontext-hardening-001` | - |
| Services and Networking (20%) | CKAD-SNW-01 Demonstrate basic understanding of NetworkPolicies | **implemented** | `kops-net-netpol-cross-namespace-001`, `kops-net-netpol-egress-dns-001`, `kops-net-netpol-ingress-repair-001` | `kops-net-netpol-create-001` |
| Services and Networking (20%) | CKAD-SNW-02 Provide and troubleshoot access to applications via services | **implemented** | `cka-net-headless-statefulset-dns-001`, `kops-net-cross-namespace-dns-001`, `kops-net-externalname-alias-001`, `kops-net-hostnetwork-dns-001`, `kops-net-multiport-service-repair-001`, `kops-net-nodeport-expose-001`, `kops-net-service-endpoint-repair-001` | `kops-net-loadbalancer-001`, `kops-multi-context-fix-001` |
| Services and Networking (20%) | CKAD-SNW-03 Use Ingress rules to expose applications | **implemented** | `kops-net-ingress-rules-001` | `cka-net-ingress-controller-routing-001` |

Domain roll-up:

| Domain | Weight | Competencies | implemented | backlog only | uncovered | validated scenarios (primary) |
|---|---|---|---|---|---|---|
| Application Design and Build | 20% | 4 | 3 | 1 | 0 | 8 |
| Application Deployment | 20% | 4 | 2 | 2 | 0 | 5 |
| Application Observability and Maintenance | 15% | 5 | 5 | 0 | 0 | 8 |
| Application Environment, Configuration and Security | 25% | 8 | 8 | 0 | 0 | 11 |
| Services and Networking | 20% | 3 | 3 | 0 | 0 | 11 |

## 4. Backlog designs

Each entry is a compact scenario design that the current backend (class `kind`, one cluster per trial, kubectl-only gateway with no stdin/files/nodes) cannot run. The task text below is a *gist*; final wording is written clean-room when the capability exists.

### Capability legend

| Code | Missing platform capability |
|---|---|
| NODE | node exec channel (ssh/docker-exec into kind node containers) plus `node.*` checks (backend class `kind-node`) (17 designs) |
| VM | full VMs for kubeadm lifecycle, OS preparation, HA (backend class `vm`) (5 designs) |
| WS | workstation with file-write, stdin/manifests, `kubectl apply -f`, openssl, helm/kustomize/podman binaries (10 designs) |
| MET | metrics-server (preloaded image, kubelet insecure-TLS patch for kind) (2 designs) |
| GW | Gateway API CRDs plus a controller (offline images) (1 designs) |
| ING | ingress controller (offline images) plus host-port mapping in the kind config (1 designs) |
| LB | LoadBalancer provider (cloud-provider-kind or MetalLB) (1 designs) |
| REG | in-cluster image registry plus a rootless builder (2 designs) |
| HELM | helm binary plus an offline chart repository mirror (2 designs) |
| MULTI | several clusters and contexts per trial (1 designs) |
| AUD | apiserver audit logging configured at cluster creation (1 designs) |
| FAULT | backend fault-injection hook (pause/stop a node container, clock skew) and cluster/node names passed to setup (2 designs) |
| CSI | a CSI driver that supports volume expansion (1 designs) |
| DNSUP | an in-cluster authoritative DNS server image (1 designs) |

### Priority order

Priority follows the CKA domain weights (Troubleshooting 30, Cluster Architecture 25, Services & Networking 20, Workloads & Scheduling 15, Storage 10) and CKAD weights (Env/Config/Security 25, Design & Build 20, Deployment 20, Services & Networking 20, Observability 15). The single capability that unlocks most designs comes first.

| Capability | Designs unlocked | Domains it opens |
|---|---|---|
| NODE | 17 | CKA:cluster-architecture, CKA:services-networking, CKA:troubleshooting, CKA:workloads-scheduling, CKAD:environment-config-security |
| WS | 10 | CKA:cluster-architecture, CKA:services-networking, CKA:storage, CKA:workloads-scheduling, CKAD:deployment, CKAD:design-build, CKAD:environment-config-security, CKAD:services-networking |
| VM | 5 | CKA:cluster-architecture, CKA:troubleshooting |
| FAULT | 2 | CKA:cluster-architecture, CKA:troubleshooting |
| HELM | 2 | CKA:cluster-architecture, CKAD:deployment |
| REG | 2 | CKA:cluster-architecture, CKAD:design-build, CKAD:environment-config-security |
| MET | 2 | CKA:troubleshooting, CKA:workloads-scheduling, CKAD:observability-maintenance |
| GW | 1 | CKA:services-networking |
| ING | 1 | CKA:services-networking, CKAD:services-networking |
| LB | 1 | CKA:services-networking, CKAD:services-networking |
| DNSUP | 1 | CKA:services-networking |
| CSI | 1 | CKA:storage |
| AUD | 1 | CKA:cluster-architecture, CKAD:environment-config-security |
| MULTI | 1 | CKA:troubleshooting, CKAD:services-networking |

Recommended order: **NODE** (`kind-node`: 14 CKA troubleshooting/architecture designs, the largest weighted gap) -> **WS** (manifest authoring unlocks the *create* variants of NetworkPolicy, PVC, Job, StatefulSet, Helm/Kustomize/operator) -> **MET** (HPA and `kubectl top`) -> **VM** (kubeadm lifecycle) -> **GW/ING/LB** (traffic through real controllers) -> the rest.

### Designs

#### `cka-trb-kubelet-stopped-001`

- **Family / profiles:** PF-NOD-001 / CKA CKA-TRB-01
- **Backend / capability:** `kind-node` / NODE; difficulty 2
- **Initial state:** 1 control-plane + 2 workers; deployment with 4 replicas spread over both workers.
- **Fault injection:** setup stops and disables kubelet.service on worker 1 (systemctl via docker exec); node goes NotReady, pods become Unknown after the eviction timeout.
- **Task gist (agent-visible):** Worker 1 is NotReady. Bring it back to Ready so that it survives a node restart, without deleting the node object.
- **Criteria, goal:** node Ready (k8s.condition); node.systemd kubelet active=true enabled=true.
- **Criteria, guards:** node object UID unchanged (not deleted/re-registered); node not cordoned or tainted by the agent; control plane untouched.
- **Negative solutions:** systemctl start kubelet without enable (not-persistent); kubectl delete node (UID guard); kubectl cordon (node still NotReady).
- **Missing capability:** A node-exec tool in the gateway (kind-node ssh/exec, forbidden-flag policy per node) and the node.systemd / node.exec check types in the verifier.

#### `cka-trb-kubelet-config-path-001`

- **Family / profiles:** PF-NOD-001 / CKA CKA-TRB-01
- **Backend / capability:** `kind-node` / NODE; difficulty 3
- **Initial state:** worker with a healthy kubelet.
- **Fault injection:** setup rewrites /var/lib/kubelet/config.yaml (wrong clientCAFile path) and restarts kubelet; kubelet logs x509/file-not-found errors, node NotReady.
- **Task gist (agent-visible):** Worker 2 will not become Ready; diagnose with the node's service logs and repair the kubelet.
- **Criteria, goal:** node Ready; node.file regex on config.yaml shows the original CA path; node.systemd kubelet active.
- **Criteria, guards:** no other key of the kubelet config changed (node.file regex per key); kubelet service enabled.
- **Negative solutions:** Replace the whole config by an empty file (kubelet fails to start); Disable client-CA authentication (config drift guard).
- **Missing capability:** NODE (journalctl + file edit on nodes), node.file contains_regex/unchanged checks.

#### `cka-trb-containerd-stopped-001`

- **Family / profiles:** PF-NOD-002 / CKA CKA-TRB-01
- **Backend / capability:** `kind-node` / NODE; difficulty 2
- **Initial state:** worker with running workloads.
- **Fault injection:** setup stops containerd on worker 1; kubelet reports container runtime not ready, node NotReady.
- **Task gist (agent-visible):** Node worker 1 is NotReady with a runtime error; find and fix the cause on the node.
- **Criteria, goal:** node Ready; node.systemd containerd active+enabled; node.exec "crictl info" succeeds.
- **Criteria, guards:** kubelet unchanged; node UID unchanged.
- **Negative solutions:** Restart kubelet only (still no runtime); drain+delete the node (UID guard).
- **Missing capability:** NODE with crictl and systemctl allowed per scenario (interfaces.allowed already lists them), node.exec.

#### `cka-trb-apiserver-flag-001`

- **Family / profiles:** PF-NOD-003 / CKA CKA-TRB-02
- **Backend / capability:** `kind-node` / NODE; difficulty 3
- **Initial state:** single control plane.
- **Fault injection:** setup edits /etc/kubernetes/manifests/kube-apiserver.yaml (--etcd-servers port typo); the apiserver crash-loops, kubectl stops working.
- **Task gist (agent-visible):** The API server is down. Restore the control plane.
- **Criteria, goal:** API reachable again (verifier call), node.file manifest has --etcd-servers=https://127.0.0.1:2379.
- **Criteria, guards:** every other apiserver flag unchanged (node.file regex set); manifest still a static pod (no Deployment workaround).
- **Negative solutions:** Delete the manifest (control plane gone); copy a manifest from another source with extra flags (flag guard).
- **Missing capability:** NODE shell with crictl/log access when kubectl is dead; agent must not rely on kubectl, so the gateway needs a node-exec channel that survives apiserver loss.

#### `cka-trb-scheduler-manifest-001`

- **Family / profiles:** PF-NOD-003 / CKA CKA-TRB-02
- **Backend / capability:** `kind-node` / NODE; difficulty 2
- **Initial state:** control plane + worker.
- **Fault injection:** setup moves kube-scheduler.yaml out of /etc/kubernetes/manifests; new Pods stay Pending with no scheduling events.
- **Task gist (agent-visible):** New Pods are never scheduled. Find the broken component and restore it.
- **Criteria, goal:** scheduler pod Ready; a verifier-created canary Pod gets scheduled; manifest back in staticPodPath.
- **Criteria, guards:** scheduler flags unchanged; no nodeName workaround on workloads (pods have no spec.nodeName set by the agent).
- **Negative solutions:** Set nodeName on each pod (guard: workloads unchanged); run a second scheduler as a Deployment (static pod guard).
- **Missing capability:** NODE (file move on control-plane node), verifier-created probe pod (net/probe pod lifecycle) for scheduling proof.

#### `cka-trb-controller-manager-001`

- **Family / profiles:** PF-NOD-003 / CKA CKA-TRB-02
- **Backend / capability:** `kind-node` / NODE; difficulty 3
- **Initial state:** Deployments exist.
- **Fault injection:** setup breaks a flag (--cluster-signing-cert-file path) in kube-controller-manager.yaml; controller-manager crash loops; Deployments no longer create ReplicaSets, CSRs never issue.
- **Task gist (agent-visible):** Scaling a Deployment has no effect. Repair the cluster component.
- **Criteria, goal:** scale test: Deployment scale-up reaches ready replicas; controller-manager pod Ready.
- **Criteria, guards:** other flags unchanged; no manual ReplicaSet/Pod creation (pod owner references must be a ReplicaSet created by the controller).
- **Negative solutions:** Create bare Pods by hand; scale RS directly (owner guard).
- **Missing capability:** NODE, k8s.count with ownerReferences filter.

#### `cka-trb-node-loss-recovery-001`

- **Family / profiles:** PF-NOD-005 / CKA CKA-TRB-01
- **Backend / capability:** `kind-node` / NODE, FAULT; difficulty 3
- **Initial state:** 2 workers, a Deployment (4 replicas) and a StatefulSet pinned by anti-affinity, pods with a long tolerationSeconds for unreachable.
- **Fault injection:** backend pauses the container of worker 2 (docker pause); pods become Unknown/Terminating-stuck.
- **Task gist (agent-visible):** Worker 2 was lost. Restore service capacity without waiting for the eviction timer.
- **Criteria, goal:** all replicas Ready on the remaining node; Service answers; lost node removed from the node list (or cordoned).
- **Criteria, guards:** no scale-down; PDB (if any) respected; no force-delete of StatefulSet pods without cause (diagnostic only).
- **Negative solutions:** scale to 0; delete the Deployment and re-create.
- **Missing capability:** FAULT (backend hook to pause/stop a node container, and the setup script needs cluster/node names, e.g. KOPS_NODE_* env), reset digest verification for node-level faults.

#### `cka-arc-etcd-snapshot-001`

- **Family / profiles:** PF-CLU-001 / CKA CKA-ARC-04
- **Backend / capability:** `kind-node` / NODE; difficulty 2
- **Initial state:** control plane with etcd static pod; some ConfigMaps as marker data.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Save an etcd snapshot to /var/backups/etcd-<id>.db on the control-plane node using the cluster's own certificates.
- **Criteria, goal:** artifact (node) validated by `etcdutl snapshot status` (revision > marker revision, total keys > 0).
- **Criteria, guards:** etcd pod untouched (node.file manifest unchanged); snapshot created after the markers (revision check).
- **Negative solutions:** touch an empty file; copy the data dir (not a snapshot, validator fails).
- **Missing capability:** NODE with etcdctl/etcdutl available on the node, artifact check with a verifier-side validator script.

#### `cka-arc-etcd-restore-001`

- **Family / profiles:** PF-CLU-002 / CKA CKA-ARC-04
- **Backend / capability:** `kind-node` / NODE; difficulty 3
- **Initial state:** snapshot taken earlier; afterwards a namespace with marker objects is deleted.
- **Fault injection:** setup deletes the namespace after taking the snapshot.
- **Task gist (agent-visible):** Restore the cluster state from the snapshot so that the deleted namespace and its objects are back.
- **Criteria, goal:** marker namespace and objects exist again; etcd static pod uses the restored data dir (node.file regex); API healthy.
- **Criteria, guards:** etcd static pod flags otherwise unchanged; snapshot file unchanged (sha256).
- **Negative solutions:** Recreate the namespace by hand (objects/UIDs differ: UID baseline recorded at snapshot time); restore into a data dir but forget to repoint the manifest.
- **Missing capability:** NODE, UID-baseline guard ("object UID equals the one recorded before deletion"), kubectl-less phase while apiserver restarts.

#### `cka-arc-cert-expiry-inspect-001`

- **Family / profiles:** PF-CLU-007 / CKA CKA-ARC-04
- **Backend / capability:** `kind-node` / NODE; difficulty 2
- **Initial state:** kubeadm-style cluster.
- **Fault injection:** none (diagnose); the answer is recorded in a ConfigMap.
- **Task gist (agent-visible):** Report which control-plane certificate expires first and its expiry date; record both in ConfigMap cert-report.
- **Criteria, goal:** ConfigMap keys equal the values computed by the verifier (node.exec kubeadm certs check-expiration).
- **Criteria, guards:** no certificate renewed or rewritten (node.file sha256 unchanged for /etc/kubernetes/pki/*).
- **Negative solutions:** Run `kubeadm certs renew all` (hash guard); guess the apiserver cert.
- **Missing capability:** NODE + kubeadm on node; computed (not static) expected values in verifier (a check comparing a ConfigMap to node.exec output).

#### `cka-arc-cert-renew-apiserver-001`

- **Family / profiles:** PF-CLU-007 / CKA CKA-ARC-04
- **Backend / capability:** `kind-node` / NODE, FAULT; difficulty 3
- **Initial state:** apiserver certificate expired by shifting the node clock (libfaketime) or by a short-lived cert issued at setup.
- **Fault injection:** setup installs an already expired apiserver serving cert and restarts the pod; kubectl fails with x509 expired.
- **Task gist (agent-visible):** Clients fail with an expired certificate error. Renew the apiserver certificate and restore access.
- **Criteria, goal:** API reachable; node.exec openssl shows notAfter in the future; cert chain still valid for the cluster CA.
- **Criteria, guards:** CA key/cert unchanged (sha256); no --insecure flags added.
- **Negative solutions:** Pass --insecure-skip-tls-verify on the apiserver manifest; replace the CA.
- **Missing capability:** NODE, FAULT (clock or cert injection), kubeadm/openssl on the node.

#### `cka-arc-apiserver-admission-plugin-001`

- **Family / profiles:** PF-CLU-008 / CKA CKA-ARC-03
- **Backend / capability:** `kind-node` / NODE; difficulty 3
- **Initial state:** default apiserver flags.
- **Fault injection:** none (modify task).
- **Task gist (agent-visible):** Enable the NamespaceAutoProvision-style (or ResourceQuota/PodNodeSelector) admission behaviour required by the task text via the apiserver flag.
- **Criteria, goal:** behavioural probe created by the verifier is mutated/denied as the plugin dictates; manifest has the flag; apiserver Ready.
- **Criteria, guards:** other admission plugins retained (flag list superset check).
- **Negative solutions:** Replace --enable-admission-plugins with only the new plugin (loses defaults).
- **Missing capability:** NODE, verifier-created probe objects, ability to restart apiserver pod safely and wait.

#### `cka-arc-kubeadm-upgrade-001`

- **Family / profiles:** PF-CLU-003 / CKA CKA-ARC-04
- **Backend / capability:** `vm` / VM; difficulty 3
- **Initial state:** kubeadm cluster at v1.34.x (1 control plane + 1 worker) with apt/offline package repo for v1.35.
- **Fault injection:** none (modify task).
- **Task gist (agent-visible):** Upgrade the control plane and the worker to v1.35.x with kubeadm, draining and uncordoning in the right order.
- **Criteria, goal:** node.exec kubectl/kubelet versions on all nodes; nodes Ready; workloads ready.
- **Criteria, guards:** workload replicas unchanged; no node removed; PDB respected during the drain (event log audit).
- **Negative solutions:** Upgrade only the control plane; skip drain; kubeadm upgrade apply with --force and a wrong version.
- **Missing capability:** VM backend (kubeadm, package repository offline mirror, two node image versions).

#### `cka-arc-kubeadm-join-worker-001`

- **Family / profiles:** PF-CLU-004 / CKA CKA-ARC-03
- **Backend / capability:** `vm` / VM; difficulty 2
- **Initial state:** control plane running; one prepared VM with runtime and kubeadm but not joined.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Add the prepared machine as a worker node using a fresh bootstrap token.
- **Criteria, goal:** node object Ready with the expected name and role label; workload scheduled on it.
- **Criteria, guards:** token TTL not infinite (kubeadm token list check); control plane unchanged.
- **Negative solutions:** Copy the admin kubeconfig onto the worker; use an expired token.
- **Missing capability:** VM backend or kind-node with a pre-baked unjoined node container (not offered by kind).

#### `cka-arc-node-prep-sysctl-001`

- **Family / profiles:** PF-CLU-005 / CKA CKA-ARC-02
- **Backend / capability:** `vm` / VM; difficulty 2
- **Initial state:** fresh VM without bridge-nf-call-iptables, ip_forward off, swap on, containerd using cgroupfs.
- **Fault injection:** OS preparation not done.
- **Task gist (agent-visible):** Prepare the machine so that kubeadm preflight checks pass.
- **Criteria, goal:** node.exec sysctl/lsmod/swapon outputs; containerd config SystemdCgroup=true; settings persistent across reboot (node.file in /etc/sysctl.d, /etc/modules-load.d).
- **Criteria, guards:** no changes to unrelated sysctls.
- **Negative solutions:** sysctl -w only (not persistent); swapoff only.
- **Missing capability:** VM backend with reboot capability for the persistence check.

#### `cka-arc-ha-add-controlplane-001`

- **Family / profiles:** PF-CLU-006 / CKA CKA-ARC-05
- **Backend / capability:** `vm` / VM; difficulty 3
- **Initial state:** single control plane with controlPlaneEndpoint set to a load balancer VIP.
- **Fault injection:** none (modify task).
- **Task gist (agent-visible):** Join a second control-plane node and verify etcd membership.
- **Criteria, goal:** 2 etcd members healthy; both apiservers behind the endpoint; node roles correct.
- **Criteria, guards:** first control plane not rebuilt; certificates reused via uploaded certs/--certificate-key (not copied by hand).
- **Negative solutions:** Join as worker; copy PKI manually then forget stacked etcd member.
- **Missing capability:** VM backend with 3+ machines and a load balancer.

#### `cka-arc-extension-interfaces-001`

- **Family / profiles:** PF-EXT-003 / CKA CKA-ARC-07
- **Backend / capability:** `kind-node` / NODE; difficulty 2
- **Initial state:** standard kind node.
- **Fault injection:** none (diagnose).
- **Task gist (agent-visible):** Report the CRI socket path, the CNI plugin conf file name and the CSI driver(s) registered; record them in a ConfigMap.
- **Criteria, goal:** ConfigMap keys equal the node-derived values (node.exec).
- **Criteria, guards:** nothing changed on the node (node.file hashes).
- **Negative solutions:** Guess common defaults (containerd.sock path differs in kind).
- **Missing capability:** NODE and verifier-computed expectations from node.exec output.

#### `cka-arc-helm-install-values-001`

- **Family / profiles:** PF-PKG-001 / CKA CKA-ARC-06; CKAD CKAD-ADP-03
- **Backend / capability:** `kind` / HELM, WS; difficulty 2
- **Initial state:** offline chart repository (KOPS-authored chart, pinned image already preloaded).
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Install the chart as release web in namespace X with replicaCount=3 and a service port override via values; upgrade once to change an image tag.
- **Criteria, goal:** helm release deployed (helm status via verifier), values as requested, pods ready; release revision 2.
- **Criteria, guards:** no hand-edited Deployment (managed-by label/ownership intact).
- **Negative solutions:** kubectl create deployment with the same name (not a release); helm template | apply (no release secret).
- **Missing capability:** helm binary in the workstation, helm-repo-mirror feature (offline repo), a release inspection check (secret type helm.sh/release.v1 decoding).

#### `cka-arc-helm-release-repair-001`

- **Family / profiles:** PF-PKG-002 / CKA CKA-ARC-06; CKAD CKAD-ADP-03
- **Backend / capability:** `kind` / HELM, WS; difficulty 3
- **Initial state:** release in failed state (bad value) with a pending-upgrade lock.
- **Fault injection:** setup performs a failed upgrade.
- **Task gist (agent-visible):** The release is failed; get it to deployed state with the correct value and keep history.
- **Criteria, goal:** release status deployed, revision incremented; pods ready.
- **Criteria, guards:** release history preserved (no uninstall/reinstall).
- **Negative solutions:** helm uninstall + install.
- **Missing capability:** HELM, WS.

#### `cka-arc-kustomize-overlay-001`

- **Family / profiles:** PF-PKG-003 / CKA CKA-ARC-06; CKAD CKAD-ADP-04
- **Backend / capability:** `kind` / WS; difficulty 2
- **Initial state:** a base directory in the workstation with a Deployment and Service; empty overlay directory.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Create an overlay that sets namespace, name prefix, replicas and an image tag patch, and apply it with kubectl -k.
- **Criteria, goal:** resulting objects in the cluster match (k8s.field) and the overlay files exist (artifact check).
- **Criteria, guards:** base unchanged (sha256).
- **Negative solutions:** edit the base in place; apply the base and patch with kubectl patch.
- **Missing capability:** WS (file-write, directories, kubectl apply -k with local paths); the Tool Gateway currently provides one kubectl command per step with no filesystem.

#### `cka-arc-operator-install-001`

- **Family / profiles:** PF-EXT-002 / CKA CKA-ARC-08; CKAD CKAD-AEC-01
- **Backend / capability:** `kind` / WS, REG; difficulty 3
- **Initial state:** operator manifests (CRD, RBAC, Deployment) and operator image preloaded.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Install the operator and create a custom resource that makes it deploy a workload with 3 replicas; change the replicas through the resource.
- **Criteria, goal:** operator pods Ready; managed Deployment has the requested replicas; scale through the CR works.
- **Criteria, guards:** managed Deployment not edited directly (managedFields/ownerReferences check).
- **Negative solutions:** Edit the managed Deployment directly; scale the operator.
- **Missing capability:** WS (apply multi-document manifests), a KOPS-authored operator image (pinned, preloaded).

#### `cka-arc-user-csr-rbac-001`

- **Family / profiles:** PF-SEC-007 / CKA CKA-ARC-01; CKAD CKAD-AEC-02
- **Backend / capability:** `kind` / WS; difficulty 3
- **Initial state:** no user exists.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Create a client certificate for user alice through a CertificateSigningRequest, approve it, grant read-only access in one namespace and produce a working kubeconfig file.
- **Criteria, goal:** can-i as alice (verifier uses the produced kubeconfig) allows get pods and denies delete; CSR approved and issued.
- **Criteria, guards:** no cluster-admin binding; kubeconfig file mode 0600.
- **Negative solutions:** Bind alice to cluster-admin; approve a CSR with signerName kubernetes.io/legacy-unknown.
- **Missing capability:** WS (openssl, file-write, kubeconfig artifact check); kubectl cannot create a CSR object imperatively.

#### `cka-net-gateway-api-httproute-001`

- **Family / profiles:** PF-NET-008 / CKA CKA-NET-04
- **Backend / capability:** `kind` / GW; difficulty 3
- **Initial state:** Gateway API CRDs and a controller installed by the backend profile; Gateway class available; two backend Services.
- **Fault injection:** none (create/repair).
- **Task gist (agent-visible):** Create a Gateway and HTTPRoute with header and path matches, then correct a route that points to the wrong Service.
- **Criteria, goal:** net.http through the Gateway address returns the right backend per match; HTTPRoute Accepted/ResolvedRefs conditions True.
- **Criteria, guards:** GatewayClass and controller untouched.
- **Negative solutions:** send everything to one backend; expose a NodePort directly.
- **Missing capability:** GW (offline controller images + CRDs, stable address reachable from the probe pod), plus manifest authoring (WS) because Gateway/HTTPRoute have no imperative create.

#### `cka-net-ingress-controller-routing-001`

- **Family / profiles:** PF-NET-007 / CKA CKA-NET-05; CKAD CKAD-SNW-03
- **Backend / capability:** `kind` / ING; difficulty 2
- **Initial state:** ingress controller installed by backend profile (pinned, preloaded).
- **Fault injection:** Ingress with wrong pathType and wrong backend port name (repair).
- **Task gist (agent-visible):** Fix the Ingress so that host/path routes reach the right Services.
- **Criteria, goal:** net.http with Host header through the controller returns the two bodies; Ingress ADDRESS populated.
- **Criteria, guards:** Services unchanged; controller unchanged.
- **Negative solutions:** delete Ingress and use NodePort; change the Services.
- **Missing capability:** ING (controller images, host port mapping in the kind config, Host-header support in net.http), plus an Ingress edit is possible with kubectl patch (spec-level variant already implemented as kops-net-ingress-rules-001).

#### `kops-net-loadbalancer-001`

- **Family / profiles:** PF-NET-002 / CKA CKA-NET-03; CKAD CKAD-SNW-02
- **Backend / capability:** `kind` / LB; difficulty 2
- **Initial state:** LoadBalancer implementation installed by the backend profile.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Expose the Deployment through a LoadBalancer Service on port 80 and wait for an external address.
- **Criteria, goal:** Service has status.loadBalancer.ingress; HTTP via that address works from the probe pod.
- **Criteria, guards:** Deployment unchanged.
- **Negative solutions:** NodePort service; ClusterIP service.
- **Missing capability:** LB (cloud-provider-kind or MetalLB images and address pool).

#### `cka-net-nodeport-from-node-001`

- **Family / profiles:** PF-NET-001 / CKA CKA-NET-03
- **Backend / capability:** `kind` / NODE; difficulty 2
- **Initial state:** Deployment and a NodePort Service exist.
- **Fault injection:** Service targetPort is wrong (repair) so that nodeIP:nodePort resets.
- **Task gist (agent-visible):** The application is not reachable on the node port from outside the pod network; fix it.
- **Criteria, goal:** net.http from the node network (hostNetwork probe or node exec curl) to <nodeIP>:<nodePort> returns 200.
- **Criteria, guards:** nodePort value unchanged; Service not re-created.
- **Negative solutions:** delete and re-create the Service with a different nodePort.
- **Missing capability:** A probe on the node network (hostNetwork probe pod or net.http `from.node` implemented through node exec). The current probe pod runs on the pod network only.

#### `cka-net-coredns-stubdomain-001`

- **Family / profiles:** PF-NET-009 / CKA CKA-NET-06
- **Backend / capability:** `kind` / DNSUP; difficulty 3
- **Initial state:** an in-cluster authoritative DNS server (answers corp.test) running as a Service.
- **Fault injection:** none (modify task).
- **Task gist (agent-visible):** Names under corp.test must resolve through that DNS server; everything else must keep using the node resolver.
- **Criteria, goal:** net.dns for host.corp.test returns the server's answer; cluster.local still resolves; Corefile still forwards to /etc/resolv.conf.
- **Criteria, guards:** kube-dns Service identity unchanged.
- **Negative solutions:** replace the default forward; add a hosts block with a static IP (answer would match only if the server's value equals it: use a changing answer).
- **Missing capability:** DNSUP (a pinned image that serves a zone; none of the preloaded images does) and Corefile edit (feasible with kubectl patch once the image exists).

#### `cka-net-cni-conf-removed-001`

- **Family / profiles:** PF-NET-011 / CKA CKA-TRB-02
- **Backend / capability:** `kind-node` / NODE; difficulty 3
- **Initial state:** new pods start normally.
- **Fault injection:** setup deletes /etc/cni/net.d/10-kindnet.conflist on worker 1 and restarts kubelet; new pods on that node stay ContainerCreating with network-plugin-not-ready.
- **Task gist (agent-visible):** Pods scheduled to worker 1 never start; find why and fix.
- **Criteria, goal:** pods on worker 1 Ready; node.file regained conf; CNI daemonset pod Running.
- **Criteria, guards:** kindnet DaemonSet unchanged; no nodeSelector workarounds on workloads.
- **Negative solutions:** cordon worker 1; copy the conflist from another node with wrong subnet (pod IP outside node CIDR check).
- **Missing capability:** NODE.

#### `cka-wl-hpa-scale-under-load-001`

- **Family / profiles:** PF-WKL-011 / CKA CKA-WLS-03
- **Backend / capability:** `kind` / MET; difficulty 3
- **Initial state:** metrics-server installed by the backend profile; Deployment with CPU requests; a load generator Deployment (busybox loop) already running.
- **Fault injection:** HPA missing/mis-targeted (scaleTargetRef wrong).
- **Task gist (agent-visible):** Make the web Deployment scale with CPU load between 2 and 6 replicas.
- **Criteria, goal:** HPA ScalingActive=True; replicas reach >=3 under load (stability window) and return to 2 after the load stops (generous settle).
- **Criteria, guards:** no manual scale; HPA bounds as specified.
- **Negative solutions:** kubectl scale to 6 (guard: replicas must be HPA-driven: HPA currentReplicas events); set minReplicas=6.
- **Missing capability:** MET (metrics-server image preloaded, --kubelet-insecure-tls for kind, aggregated API ready before setup), tolerant timing windows.

#### `cka-trb-resource-usage-top-001`

- **Family / profiles:** PF-OBS-003 / CKA CKA-TRB-03; CKAD CKAD-AOM-03
- **Backend / capability:** `kind` / MET; difficulty 2
- **Initial state:** three pods with very different CPU usage (busy loop vs idle).
- **Fault injection:** none (diagnose).
- **Task gist (agent-visible):** Identify the pod that consumes the most CPU with kubectl top and label it hot=true.
- **Criteria, goal:** exactly one pod labelled hot=true and it is the busy one.
- **Criteria, guards:** pods unmodified otherwise.
- **Negative solutions:** label by name guess; label all.
- **Missing capability:** MET.

#### `kops-wl-statefulset-create-001`

- **Family / profiles:** PF-WKL-007 / CKA CKA-WLS-04; CKAD CKAD-ADB-02
- **Backend / capability:** `kind` / WS; difficulty 2
- **Initial state:** namespace with a headless Service.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Create a StatefulSet with 3 replicas, ordered startup, and a 1Gi volumeClaimTemplate; verify per-pod storage identity.
- **Criteria, goal:** three pods Ready in order; three PVCs bound; per-pod DNS resolves.
- **Criteria, guards:** Service unchanged.
- **Negative solutions:** Deployment with a shared PVC; Parallel pod management when Ordered is required.
- **Missing capability:** WS or a stdin/-f capability (StatefulSet has no imperative kubectl create); kubectl apply -f - is blocked by the gateway (no stdin, no heredocs).

#### `kops-net-netpol-create-001`

- **Family / profiles:** PF-NET-004 / CKA CKA-NET-02; CKAD CKAD-SNW-01
- **Backend / capability:** `kind` / WS; difficulty 2
- **Initial state:** three namespaced app tiers, no policies.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Author default-deny plus tier-to-tier allow policies so that only front->api and api->db are possible.
- **Criteria, goal:** positive and negative probes (all 6 tier pairs) behave as required.
- **Criteria, guards:** no policy in other namespaces; default-deny present.
- **Negative solutions:** only allow policies (nothing isolated); allow-all ipBlock 0.0.0.0/0.
- **Missing capability:** WS (NetworkPolicy has no imperative create). The repair/modify variants are implemented (kops-net-netpol-*).

#### `kops-sto-pvc-create-mount-001`

- **Family / profiles:** PF-STO-004 / CKA CKA-STO-01; CKAD CKAD-ADB-04
- **Backend / capability:** `kind` / WS; difficulty 2
- **Initial state:** default StorageClass standard (local-path).
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Create a 2Gi ReadWriteOnce claim and a Deployment that mounts it at /data; data must survive a pod restart.
- **Criteria, goal:** PVC Bound with the requested size; file written by pod 1 is read by the restarted pod.
- **Criteria, guards:** storageClassName not forced to a nonexistent class.
- **Negative solutions:** emptyDir; hostPath.
- **Missing capability:** WS (PVC and volume wiring need a manifest; no imperative PVC create). The reference-repair variants are implemented.

#### `kops-wl-job-parallel-completions-001`

- **Family / profiles:** PF-WKL-005 / CKA CKA-WLS-04; CKAD CKAD-ADB-02
- **Backend / capability:** `kind` / WS; difficulty 2
- **Initial state:** namespace.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Run a Job with 6 completions, parallelism 2, backoffLimit 1 and a 120 s deadline that prints indexed lines.
- **Criteria, goal:** Job Complete with succeeded=6; max concurrent pods never above 2 (sampled).
- **Criteria, guards:** ttl not set to 0 (artifact must remain).
- **Negative solutions:** 6 separate pods; CronJob.
- **Missing capability:** WS (kubectl create job has no flags for completions/parallelism; spec fields completions are immutable so a patch cannot fix a wrong create).

#### `kops-sto-pvc-expand-001`

- **Family / profiles:** PF-STO-001 / CKA CKA-STO-01
- **Backend / capability:** `kind` / CSI; difficulty 3
- **Initial state:** StorageClass with allowVolumeExpansion backed by a CSI driver that supports expansion.
- **Fault injection:** PVC at 1Gi, pod running.
- **Task gist (agent-visible):** Grow the claim to 2Gi while the pod keeps running.
- **Criteria, goal:** PVC capacity 2Gi (status), filesystem resized (pod df check).
- **Criteria, guards:** PVC UID unchanged; pod not restarted.
- **Negative solutions:** delete and recreate the PVC.
- **Missing capability:** CSI (rancher local-path does not support expansion), WS not needed.

#### `cka-sec-audit-who-deleted-001`

- **Family / profiles:** PF-SEC-003 / CKA CKA-ARC-01; CKAD CKAD-AEC-02
- **Backend / capability:** `kind-node` / AUD, NODE; difficulty 3
- **Initial state:** apiserver audit log enabled; a ServiceAccount deleted a ConfigMap earlier.
- **Fault injection:** none (diagnose).
- **Task gist (agent-visible):** Find from the audit log which identity deleted ConfigMap X and grant nothing; record the identity in a ConfigMap.
- **Criteria, goal:** ConfigMap value equals the true user (verifier computes from the audit log).
- **Criteria, guards:** audit policy and log untouched (node.file hashes).
- **Negative solutions:** guess; read RBAC bindings instead.
- **Missing capability:** AUD (kind config extraMounts/kubeadmConfigPatches for audit flags at create time), NODE (read the log).

#### `ckad-img-build-push-001`

- **Family / profiles:** PF-IMG-001 / CKAD CKAD-ADB-01
- **Backend / capability:** `kind` / REG, WS; difficulty 2
- **Initial state:** build context in the workstation; in-cluster registry reachable as registry.kops:5000.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Build an image from the supplied Dockerfile with a build argument, tag it, push it to the registry and deploy it.
- **Criteria, goal:** registry catalog has the tag; Deployment runs it; HTTP body shows the build arg.
- **Criteria, guards:** Dockerfile unchanged except where the task allows.
- **Negative solutions:** use a public image; docker save/load into nodes directly.
- **Missing capability:** REG (registry + rootless builder), WS (file-write, podman/buildah).

#### `kops-multi-context-fix-001`

- **Family / profiles:** PF-NET-003 / CKA CKA-TRB-05; CKAD CKAD-SNW-02
- **Backend / capability:** `kind` / MULTI; difficulty 3
- **Initial state:** two clusters (dev, prod) with contexts; the same app broken in only one.
- **Fault injection:** Service selector wrong in the cluster named in the task.
- **Task gist (agent-visible):** Switch to context prod and repair the Service there (do not touch dev).
- **Criteria, goal:** prod Service endpoints ready; dev unchanged (state digest).
- **Criteria, guards:** dev cluster state hash unchanged; no context changes outside the task.
- **Negative solutions:** fix dev instead; fix both.
- **Missing capability:** MULTI (several clusters per trial, kubeconfig with named contexts, gateway support for `config use-context`, per-cluster verifier credentials; design K.3).

#### `cka-sch-static-pod-001`

- **Family / profiles:** PF-SCH-007 / CKA CKA-WLS-04
- **Backend / capability:** `kind-node` / NODE; difficulty 2
- **Initial state:** worker node.
- **Fault injection:** none (create task).
- **Task gist (agent-visible):** Run a static pod named X on worker 1 using the kubelet's static pod path.
- **Criteria, goal:** mirror pod X-<node> Running; manifest file in staticPodPath on the node.
- **Criteria, guards:** no Deployment/DaemonSet workaround (ownerReference kind Node).
- **Negative solutions:** kubectl run with nodeName; Deployment pinned with nodeSelector.
- **Missing capability:** NODE (write a manifest file on the node), node.file check.

#### `cka-trb-node-pressure-evict-001`

- **Family / profiles:** PF-NOD-004 / CKA CKA-TRB-01
- **Backend / capability:** `vm` / VM; difficulty 3
- **Initial state:** worker with small root disk.
- **Fault injection:** setup fills the disk below the eviction threshold; node reports DiskPressure and evicts pods.
- **Task gist (agent-visible):** Pods keep getting evicted from worker 1; find the cause and fix it.
- **Criteria, goal:** node DiskPressure False; workload stable over a window.
- **Criteria, guards:** workloads not deleted; kubelet eviction thresholds unchanged.
- **Negative solutions:** raise eviction thresholds; cordon only.
- **Missing capability:** VM (real disk/kernel behaviour); kind nodes share the host filesystem.

### Runnable on the current backend but not authored yet

These need no new platform capability. They were left out only for time; each can be authored with the existing check vocabulary (see section 5). The count is part of the "ideas" pool, not of the backlog total above.

| Idea (proposed id) | Family | Competency | Mode | Sketch |
|---|---|---|---|---|
| `kops-wl-native-sidecar-001` | PF-WKL-008 | CKA-WLS-04 / CKAD-ADB-03 | modify | Convert a regular sidecar into a native sidecar (init container with `restartPolicy: Always`) so that the Job it belongs to can complete; check Job Complete and sidecar logs. |
| `kops-net-service-named-port-001` | PF-NET-003 | CKA-TRB-05 / CKAD-SNW-02 | repair | Two-port Service whose `targetPort` names do not match the container port names; `k8s.endpoints` per port plus HTTP on both. |
| `kops-net-session-affinity-001` | PF-NET-001 | CKA-NET-03 / CKAD-SNW-02 | modify | Enable ClientIP affinity with a timeout; behavioural check: 10 requests from one client pod return one pod name. |
| `cka-sec-aggregated-clusterrole-001` | PF-SEC-002 | CKA-ARC-01 | create | Label a custom ClusterRole into the `edit` aggregation; `k8s.can_i` as a user bound to `edit`. |
| `kops-res-limitrange-max-001` | PF-CFG-005 | CKA-WLS-05 / CKAD-AEC-03 | repair | Pods rejected by a LimitRange max; fix the Deployment, keep the LimitRange (same shape as the ResourceQuota scenario, different admission message). |
| `kops-job-suspend-ttl-001` | PF-WKL-005 | CKA-WLS-04 / CKAD-ADB-02 | modify | Patch a suspended Job to run, then set `ttlSecondsAfterFinished` so it is garbage collected (needs a settle window). |
| `kops-wl-daemonset-rolling-001` | PF-WKL-007 | CKA-WLS-04 | modify | Change a DaemonSet `updateStrategy` (`maxUnavailable`) and roll an image, checking `updatedNumberScheduled` on 2 workers. |
| `cka-sch-pod-anti-affinity-001` | PF-SCH-003 | CKA-WLS-05 | modify | Required pod anti-affinity by hostname so replicas land on different workers (needs `workers: 2`). |
| `ckad-cfg-projected-volume-001` | PF-CFG-003 | CKAD-ADB-04 | modify | Merge a ConfigMap and a Secret into one projected volume; HTTP check of both files. |
| `kops-cfg-immutable-configmap-001` | PF-CFG-001 | CKA-WLS-02 / CKAD-AEC-05 | modify | Rotate an `immutable: true` ConfigMap by creating a versioned copy and re-pointing the Deployment (single `kubectl create configmap` plus patch). |
| `kops-sec-imagepullsecret-001` | PF-CFG-002 | CKAD-AEC-06 | create | `kubectl create secret docker-registry`, attach to a ServiceAccount; spec-only (no private registry). |
| `kops-obs-jsonpath-report-001` | PF-OBS-006 | CKA-TRB-03 / CKAD-AOM-03 | diagnose | Record in a ConfigMap the pod with the most restarts and the Nodes' kubelet versions using `-o jsonpath` / `--sort-by`; expected values are static per seed. |
| `kops-net-netpol-ipblock-egress-001` | PF-NET-005 | CKA-NET-02 / CKAD-SNW-01 | repair | Egress policy with a wrong `ipBlock` CIDR/except for an in-cluster server; positive and negative probes. |
| `kops-trb-debug-ephemeral-001` | PF-OBS-004 | CKAD-AOM-05 | diagnose | Use `kubectl debug` with an ephemeral container to read a file from a shell-less pod; record the value. Needs a check that the gateway allows non-interactive `debug`. |


## 5. Infrastructure changes and new check types

All changes are additive. `.venv/bin/pytest -q` stays green (the new unit tests live in `tests/test_checks.py`; the existing e2e test is skipped without `KOPS_E2E=1`), and `kops-net-service-endpoint-repair-001` was re-run through `kops selftest` after the changes (section 2).

### 5.1 Verifier (`src/kops/verifier.py`)

| Check / feature | Notes |
|---|---|
| JSONPath subset (`select`, `parse_path`) | `.a.b`, `[0]`, `[-1]`, `[*]`, filters `[?(@.name=="x")]` (`==`/`!=`), quoted keys `["a.b/c"]`. Used by every `k8s.*` check and by `k8s.unchanged`. |
| `k8s.field` | now accepts `jsonpath` (schema name) and `path` (the old verifier name); operators `eq ne in not_in regex exists absent gte lte contains subset` and new `qty_eq/qty_gte/qty_lte` (Kubernetes quantities: `128Mi`, `500m`); resource refs by name, by label `selector`, or all objects of a kind; `all_items` (default true) controls multi-value paths and multi-object refs. A missing object is a FAIL (agent state), never an ERROR. |
| `k8s.exists` | `present` / `absent`, by name or selector. |
| `k8s.count` | objects of a kind (+ selector) with an optional `field_filter` (`<path>==<value>` or `!=`, scalar types compared leniently so `==true` matches the string "true"). |
| `k8s.condition` | `.status.conditions[type]` equals True/False/Unknown on every addressed object. |
| `k8s.can_i` | `kubectl auth can-i --as=... [--subresource] [-n]` run as verifier-admin; anything other than a clear `yes`/`no` answer is an ERROR (INVALID trial). |
| `k8s.logs` (**new type**, schema updated) | `kubectl logs <kind>/<name>` or by selector, `container`, `previous`, `tail`, `regex`, `min_matches`, `expect: match|no_match`. "Waiting to start"-class errors are FAIL; connection-class errors are ERROR. |
| `k8s.placement` (**new type**, schema updated) | Running pods of a selector and the nodes they are on: `min_pods`, `node_selector` + `mode: within|outside`, `max_per_node`, `min_distinct_nodes`. Used for scheduling, taints, drain and spread scenarios. |
| `k8s.rollout_complete` | accepts the schema's `resource` ref (still accepts `name`/`namespace`). |
| `net.http` | now honours `status`, `body_regex` and the `from` block: default is the verifier probe pod; `from.labels` / `from.pod` / `from.container` run the request from a scenario-owned client pod (needed for NetworkPolicy positive and negative probes). Implemented with `wget -S` and parsed status lines. The old implementation ignored `status` and `from`. |
| `net.tcp`, `net.dns` | busybox `nc -z` and `nslookup`; `answer_regex` supported. |
| `stability` | nested check sampled `samples` times over `window_seconds`; any failing sample fails the criterion. |
| `k8s.unchanged` | `scope: spec|spec+metadata.labels|data` shorthands in addition to `jsonpaths`; paths use the new engine. |

Tri-state semantics are unchanged: infrastructure problems (probe pod cannot exec, unusable can-i output, unparsable path) raise `CheckError` and make the trial INVALID.

### 5.2 Schema (`schemas/criteria.schema.json`)

Added `k8s.logs` and `k8s.placement`, `from.pod` / `from.container` for the `net.*` probes, and the `qty_*` operators for `k8s.field`. The schema remains valid (checked on every `kops lint`).

### 5.3 Backend (`src/kops/backend_kind.py`, `src/kops/runner.py`, `src/kops/lab.py`)

- `backend.topology.workers` is now honoured: `KindCluster(name, workers=N)` writes a kind config with `N` worker nodes, waits for all nodes Ready, and removes the config on delete. `runner.py` and `lab.py` each gained one argument (`workers=scn.raw["backend"]["topology"]["workers"]`); trial semantics are untouched.
- With workers the verifier's probe pod is pinned to the control plane (with the control-plane toleration), so `kubectl drain`/`cordon` of a worker can never evict or break the verifier's client. (Found by the drain scenario's selftest: the bare probe pod blocked `drain` on one of three runs.)
- No new images: every scenario uses `busybox:1.36.1` and `agnhost:2.53` only, so the preloaded list is unchanged. Cluster creation with 1-3 workers costs about 35-60 s.

### 5.4 Lint (`src/kops/lint.py`)

`kops lint` now also runs `lint_content`, for each seed: every template token in fixtures/setup/reference files resolves; rendered fixtures parse as YAML; every line of `reference/solution.sh` and `reference/wrong-*.sh` is a single plain `kubectl` command that the gateway would accept (no shell tokens, no forbidden flags such as `--as`); and the `fail` rules of `docs/contamination-denylist.yaml` (literal, namespace-context and resource-name-context tokens) do not match any scenario file. Three authoring bugs (a missing `port` parameter in three scenarios, a reference command with `--as`, a brace-escaping slip) would have been caught by it earlier.

### 5.5 Existing scenario

`kops-net-service-endpoint-repair-001` declared `topology.workers: 2` although the backend ignored it; it is now `workers: 0` so that its behaviour (single-node cluster) is unchanged. Its selftest was re-run after all infrastructure changes.

### 5.6 Authoring rules learned from the runtime (for the next scenario author)

1. `setup.confirm.must_fail` is evaluated per **criterion**: every criterion of every listed invariant must FAIL on the prepared state. An invariant that mixes a failing and an initially-passing criterion makes the trial INVALID (`setup_confirm_failed`); split such criteria into a guard invariant listed in `must_pass`.
2. Every scenario needs a `ns` parameter (the runner snapshots that namespace); cluster-scoped scenarios still carry one.
3. Reference and wrong-fix files are replayed through the gateway: no pipes, no `&&`, no heredocs, no `--as`, no stdin; JSON bodies go in single quotes; a command the gateway rejects does **not** fail the oracle (it is just a rejected step), so `lint_content` is the only safety net.
4. FAIL trials always wait for the whole settle window (`verification.settle.max_wait_seconds`), so selftests of scenarios with `settle: true` criteria take 4-5 minutes at `--jobs 2`.
5. Creation tasks are limited to objects kubectl can create imperatively (Deployment, Service, ConfigMap, Secret, ServiceAccount, Role, RoleBinding, ClusterRole, ClusterRoleBinding, CronJob, Job, PDB, PriorityClass, Ingress, Namespace, `autoscale`, `expose`, `run`). NetworkPolicy, PVC/PV/StorageClass, StatefulSet, DaemonSet, LimitRange, CRs have no imperative create: their scenarios are *repair/modify* variants, and the create variants are backlog items needing the `WS` capability.


## 6. Problems found, validation scope and mapping decisions

### 6.1 Validation scope: kind only

Every selftest in section 2 ran on the `kind` backend only (kindest/node v1.35.8, kindnet CNI, rancher local-path StorageClass, kube-proxy in iptables mode, containerd 2.3.4). **None has been validated on a kubeadm VM sandbox.** A re-validation (`kops selftest` with the future VM backend) is required before any scenario is frozen. Scenarios whose behaviour is most likely to differ on a kubeadm cluster:

| Area | Scenarios | Why it may differ |
|---|---|---|
| CNI and NetworkPolicy enforcement | `kops-net-netpol-ingress-repair-001`, `kops-net-netpol-cross-namespace-001`, `kops-net-netpol-egress-dns-001`, `kops-net-hostnetwork-dns-001`, `cka-net-headless-statefulset-dns-001` | kindnet enforces policies (probed positive and negative); a kubeadm cluster with Flannel or no policy engine would not. Pod CIDR 10.244.0.0/16 is hard-coded in the headless-DNS answer regex. Egress to CoreDNS assumes the DNS pods are in `kube-system`. |
| Storage class and volumes | `cka-sto-default-class-001`, `cka-sto-pv-bind-repair-001`, `cka-sto-reclaim-retain-001`, `kops-sto-pvc-reference-repair-001`, `cka-arc-extension-interfaces-report-001` | Assume a `standard` class with provisioner `rancher.io/local-path`, WaitForFirstConsumer binding, and hostPath PVs under `/tmp/kops`. The interfaces report uses literals tied to the node image (`containerd://2.3.4`, `kindnet`). |
| Node layout and control plane | `cka-sch-*` (nodeselector, taint, drain, spread), `cka-wl-daemonset-controlplane-001`, `cka-trb-node-unschedulable-001`, `cka-trb-node-capacity-diagnose-001`, `cka-net-kubeproxy-rollout-undo-001`, `cka-net-coredns-two-layer-repair-001` | Assume node names/labels of kind, the `node-role.kubernetes.io/control-plane` taint and label, workers discovered by `!node-role...`, kube-proxy as a DaemonSet with container `kube-proxy`, CoreDNS Corefile layout and `reload` timing (about 100 s) and a single-node control plane. |
| Probe and image assumptions | all `net.http` scenarios | Verifier probe pod and all images are preloaded; a VM sandbox must provide the same offline images. |
| API-level assumptions | `kops-sec-pss-restricted-001`, `cka-wl-hpa-spec-001`, `kops-net-ingress-rules-001` | PSA enabled by default (true on 1.35 kubeadm), no metrics-server and no ingress controller (spec-only checks). |

### 6.2 Runtime and tooling problems

1. **`setup.confirm.must_fail` is per criterion** (every criterion of a listed invariant must fail). This caused 7 authoring failures, all fixed by moving initially passing criteria into guard invariants. Worth stating in `docs/scenario-schema.md` (not edited here).
2. **`k8s.field` schema/verifier mismatch**: the schema calls the path `jsonpath`, the old verifier read `path`; and the old `net.http` ignored `status` and `from`. Both fixed (section 5).
3. **Gateway forbids `--as`**, so an agent cannot run `kubectl auth can-i --as=system:serviceaccount:...`, the natural verification tool for RBAC tasks. The three RBAC scenarios still work (agents can read Roles/Bindings), but this makes them harder than intended. Recommendation: allow read-only `auth can-i --as`. Hints mention `--as` for human lab mode.
4. **Gateway has no stdin/files**, so creation tasks for NetworkPolicy, PVC/PV, StatefulSet, DaemonSet, Job parallelism etc. are impossible; only repair/modify variants exist (section 4, capability WS).
5. **Bare probe pod blocked `kubectl drain`** on one of three runs of the drain scenario (random placement); fixed by pinning the probe to the control plane when workers exist.
6. **Infra flake**: one trial of `cka-trb-node-capacity-diagnose-001` ended INVALID (`provision_failed`: kind picked a host port that another concurrently created cluster had just taken). Not a scenario defect; the re-run passed. Parallel selftests could retry `kind create` on port conflicts.
7. **CoreDNS ConfigMap changes take about 100 s** to be loaded (kubelet sync plus `reload`); the CoreDNS scenario's setup restarts CoreDNS so the broken Corefile is active before the agent starts. An earlier version let a "Service-only" fix pass because the break was not yet active.
8. **CoreDNS answers per-pod names for ClusterIP Services too**, so the headless scenario checks the Service-name lookup (two pod addresses) rather than pod names.
9. **`kubectl set resources --limits=memory=0` yields a zero limit (= unlimited)**; the OOM scenario needed an extra lower-bound guard (found by its wrong-fix).
10. **Terminating pods linger up to 30 s** (busybox httpd ignores SIGTERM) and keep old restart counts in selector-based checks; criteria on "current pods" therefore use `settle`. Rolling updates with topology spread leave an uneven result (3/1), so that scenario uses `Recreate`.
11. **Selftest duration**: every FAIL trial waits the full settle window; 4-6 minutes per scenario at `--jobs 2`. A `--settle-cap` for selftests would cut this by about half.
12. `kubectl autoscale --cpu-percent` is deprecated in kubectl 1.35 (warning only); the HPA scenario uses `--cpu=N%`.

### 6.3 Weak or partial verification (honest labelling)

- `kops-net-ingress-rules-001`, `cka-wl-hpa-spec-001`, `cka-sto-default-class-001`: object/spec checks only (no controller, no metrics, no claim creation possible). Tagged `spec-only` where applicable.
- `ckad-obs-api-deprecation-001`: data-only check on ConfigMap text; manifests are not applied.
- Diagnosis scenarios (`*-report-*`, `*-findings-*`, `kops-ext-crd-discover-001`, `ckad-obs-cli-report-001`, `cka-trb-node-capacity-diagnose-001`) verify recorded answers, not skills in progress; `value_from` compares answers with live state where values are dynamic.
- Reference solutions of scenarios whose answers are dynamic use literals fixed by the pinned node image.

### 6.4 Mapping decisions

- `cka-net-kubeproxy-rollout-undo-001` maps to CKA-TRB-02 although the catalog puts PF-NET-011 on `kind-node`: this variant is repairable with kubectl alone (DaemonSet rollback).
- `cka-sch-drain-maintenance-node-001` maps to CKA-ARC-04 (cluster lifecycle: node maintenance) as in the catalog's PF-SCH-006.
- `cka-trb-node-unschedulable-001` maps to CKA-TRB-01 for its API-level part; node-process faults stay in the backlog.
- Dual-profile scenarios use the `kops-` prefix; profile-specific ones use `cka-`/`ckad-` (e.g. PDB, drain, taints are CKA-only per the catalog).
- Scenario ids mix CKA and CKAD competencies only through `kops-` scenarios; secondary competencies are not recorded.
- Flaky scenarios: none observed in 3 oracle replays each, except the single infra flake above.

