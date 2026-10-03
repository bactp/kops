# Operations runbook (v0.1)

All commands run from a workstation that has `kubectl` (1.35), `docker`, and ssh access to the workers. The host cluster
needs KubeVirt, CDI, a CSI snapshot controller and Longhorn (see `docs/simulator-design.md` §11 for what was installed
and how it was measured).

## 1. Golden node image (once per Kubernetes version or image change)
```bash
# on a cluster node (needs to reach VM pod IPs); copy scripts/golden there first
VERSION=v3 BASE_PVC=ubuntu-base scripts/golden/build-golden-disk.sh      # PVC golden/node-golden-v3
VERSION=v3 scripts/golden/convert-golden.sh                               # qcow2 on worker-1 (several minutes)
# on the workstation
KEY=~/workflow-prj.pem WORKERS="<worker ips>" VERSION=v3 SRC_HOST=<worker-1 ip> scripts/golden/publish-golden.sh
```
The image holds containerd, kubeadm/kubelet/kubectl, Calico, local-path-provisioner (as the default class `standard`),
the container images the scenarios use (busybox 1.36.1, agnhost 2.53), and the candidate tools (vim, yq, jq, curl, wget,
man, completion, alias `k`). The sandbox has no internet, so everything a scenario needs must be in this image.

## 2. Platform image and deployment
```bash
KEY=~/workflow-prj.pem WORKERS="<worker ips>" scripts/build-image.sh          # docker build + import into containerd
KUBECONFIG=~/kops-k8s.kubeconfig NODE_IP=<node ip> ADMIN_USERS=<username> scripts/deploy.sh
```
Dashboard `http://<node ip>:30800`, Keycloak `http://<node ip>:30880` (admin user `kcadmin`, password in
`~/.kops-secrets/keycloak-admin.password`). Register an account on the login page; it is an admin if its username is in
`ADMIN_USERS`. To publish a changed catalogue (`catalog/*.txt`) run `scripts/deploy.sh` again (ConfigMap + restart).

## 3. Validate scenarios on the real sandbox
```bash
KUBECONFIG=~/kops-k8s.kubeconfig SHARDS=2 WORKERS=0 RUN=r1 scripts/selftest-vm.sh   # parallel Jobs, about 5 min per scenario
kubectl -n kops-gw wait --for=condition=complete --timeout=8h job -l app=kops-selftest
RUN=r1 scripts/collect-selftest-vm.sh                                              # updates catalog/*.txt, failures in deploy/out/
```
A scenario enters `catalog/available.txt` only if the negative control holds, the null agent and every wrong fix FAIL,
the oracle PASSes twice. It enters `catalog/reset-api.txt` only if the API-level reset returned the cluster to the baseline
digest after every trial; otherwise the cluster is recreated between tasks.
Scenarios with extra workers are validated with `WORKERS=1|2|3` (separate runs).

## 4. End-to-end check of a deployment
```bash
KC_ADMIN_PASSWORD=$(cat ~/.kops-secrets/keycloak-admin.password) PLATFORM=http://<node ip>:30800 AUTH=http://<node ip>:30880 \
  .venv/bin/python scripts/e2e-platform.py [scenario-id]
```
Creates a throwaway user, logs in through Keycloak, starts a session, solves the task by typing into the terminal WebSocket,
checks, restarts, deletes. Prints PASS/FAIL per step.

## 5. Debugging
- `KOPS_KEEP_FAILED=1` on the platform deployment keeps a sandbox whose provisioning failed. Enter it from the platform pod:
  `kubectl -n kops-gw exec deploy/kops-platform -- ssh -i /var/run/kops/<ns>/platform.key ubuntu@<vm ip>`.
- Sandboxes carry the label `kops.io/managed=true`; selftest sandboxes also `kops.io/exempt=true` (the sweeper leaves them
  alone, so delete them by hand if a run is aborted: `kubectl delete ns -l kops.io/exempt=true`).
- Problems found while building v0.1 and fixed: the sweeper removed selftest sandboxes; the platform could not ssh to nodes
  (policy); blocked DNS made every lookup in the guest wait (kubeadm timed out); the ssh config on `base` was written with
  literal `\n`. Each has a regression test or a note in the code.

## 6. Warm pool

`KOPS_WARM_POOL_SIZE` (ConfigMap `kops-platform`, default 1) is the number of idle single-node clusters the platform keeps ready. A practice session whose scenario needs no extra worker takes one at once (the log shows "using a pre-provisioned cluster") and the pool is refilled in the background; Playground and multi-worker scenarios still provision a new sandbox. Each idle cluster holds about 4 GiB of node memory, so keep the number small. An idle sandbox is evicted when a session that cannot use it needs the room. Pool sandboxes are labelled `kops.io/session=warm-<id>` (ready) or `pool-<id>` (being built); the sweeper never touches them, and the platform removes half-built ones at start. `GET /api/admin/capacity` reports `warm_pool: {target, ready, filling}`. After a failed build the pool waits two minutes before trying again.

Not done on purpose (few users for now): sizing the pool by load, one pool per scenario family, and scheduled refresh of old idle clusters. See the scaling notes in `docs/simulator-design.md` §12.
