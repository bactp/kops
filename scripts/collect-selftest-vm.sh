#!/usr/bin/env bash
# Read the SUMMARY lines of the finished selftest jobs of one RUN and merge them into catalog/*.txt.
set -euo pipefail
cd "$(dirname "$0")/.."
RUN="${RUN:?set RUN}"; OUT=deploy/out
python3 - "$RUN" <<'PY'
import json, pathlib, subprocess, sys
run = sys.argv[1]
jobs = pathlib.Path(f"deploy/out/selftest-{run}.jobs").read_text().split()
passed, failed, api = set(), {}, set()
for j in jobs:
    log = subprocess.run(["kubectl", "-n", "kops-gw", "logs", f"job/{j}"], capture_output=True, text=True).stdout
    for line in log.splitlines():
        if line.startswith("SUMMARY "):
            s = json.loads(line[8:]); passed |= set(s["passed"]); api |= set(s["reset_api"]); failed.update(s["failed"])
def merge(path, ids, header):
    p = pathlib.Path(path); old = [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")] if p.exists() else []
    p.write_text(header + "\n".join(sorted(set(old) | ids)) + "\n")
merge("catalog/available.txt", passed, "# Scenario ids the KubeVirt provider can run (maintained by scripts/collect-selftest-vm.sh).\n")
merge("catalog/reset-api.txt", api, "# Scenario ids whose API-level reset was proven by `kops selftest-vm`.\n")
pathlib.Path(f"deploy/out/selftest-{run}.failed.json").write_text(json.dumps(failed, indent=1))
print(f"passed {len(passed)}, reset=api {len(api)}, failed {len(failed)} (details in deploy/out/selftest-{run}.failed.json)")
PY
