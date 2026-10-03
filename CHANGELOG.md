# Changelog

## 0.1.0 (unreleased)

First platform release: **Practice mode and Playground on KubeVirt sandboxes, with a web dashboard and accounts.**

### Added
- **Sandbox**: `KubeVirtProvider` (one namespace per session; `base`, `cp-1` and optional workers booted from a golden `containerDisk` image; kubeadm cluster formed per session; default-deny NetworkPolicies; verifier credential minted per session and never stored in the VMs). `KindProvider` for development and CI, `FakeProvider` for tests.
- **Platform API** (FastAPI, SQLite): OIDC login (authorization code + PKCE), owned sessions, one active session per user, TTL and extension, capacity check, orphan sweeper, progress, admin endpoints, SSE session events, terminal WebSocket (pty over ssh to `base`, hop to the cluster node). Contract in `docs/platform-api.md`.
- **Dashboard** (`web/`, no build step): task list with filters, task pane with live provisioning log, CHECK with per-criterion evidence, three hints, solution (marks the attempt assisted), Next/Restart task, browser terminal tabs (xterm.js), Playground, progress, admin view.
- **Reset**: API-level reset (`src/kops/reset.py`) so a session can move to the next task without rebuilding the cluster when the scenario has proven it restores the baseline; otherwise the cluster is recreated.
- **Validation on the real sandbox**: `kops selftest-vm` (negative control, null agent, wrong fixes, oracle twice, reset digest check) runs as parallel Jobs (`scripts/selftest-vm.sh`) and maintains `catalog/available.txt` and `catalog/reset-api.txt`.
- **Packaging and deployment**: `Dockerfile`, `deploy/k8s/` (RBAC, platform, bundled Keycloak with self-registration, selftest Job), `scripts/build-image.sh`, `scripts/deploy.sh`, golden image pipeline in `scripts/golden/`, end-to-end check `scripts/e2e-platform.py`.
- **Warm pool** (`KOPS_WARM_POOL_SIZE`, default 1 in the manifests): idle, ready-made single-node clusters; a practice session takes one instead of provisioning (about 2 minutes saved), and the pool refills in the background. **Faster API reset**: the cluster state is collected with one `kubectl` call and pods of removed namespaces are force-deleted (measured 8 s instead of 36 to 60 s).
- 60 scenarios for CKA and CKAD (kind-validated); the catalogue shown to users is limited to those validated on KubeVirt.

### Known limitations (planned for later releases, see `docs/simulator-design.md` §12)
- No Mock Exam, offline docs mirror or in-browser editor (v0.2). No strict exam environment profile.
- Scenarios that change nodes, `kube-system` or shared cluster-scoped state, and scenarios needing several clusters, are not offered yet (v0.2 / v0.3).
- SQLite instead of Postgres; HTTP only; Keycloak in dev mode; images are imported into containerd on each worker (no registry); the platform ClusterRole is broad.
- DNS egress to the host cluster's CoreDNS is allowed from sandboxes (DNS tunnelling is theoretically possible).
- Node capacity is small: about 4 concurrent sessions on two 16 GiB workers.
