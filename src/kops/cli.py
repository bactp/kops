from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["selftest-vm"]:          # has its own options (--workers, --out, --provider)
        from .vmselftest import main as vm_main
        return vm_main(args[1:])
    ap = argparse.ArgumentParser(prog="kops")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("lint"); s.add_argument("scenario")
    s = sub.add_parser("selftest"); s.add_argument("scenario")
    s.add_argument("--seed", type=int, default=1); s.add_argument("--repeats", type=int, default=3)
    s.add_argument("--jobs", type=int, default=3)
    s = sub.add_parser("run"); s.add_argument("experiment"); s.add_argument("--jobs", type=int, default=2)
    s = sub.add_parser("lab"); s.add_argument("action", choices=["up", "verify", "down", "task"])
    s.add_argument("scenario"); s.add_argument("--seed", type=int, default=1)
    s.add_argument("--wait", action="store_true", help="verify: poll up to the scenario settle time")
    s = sub.add_parser("compare"); s.add_argument("results_dir")
    s = sub.add_parser("selftest-vm", help="selftest on a provider sandbox, reusing one cluster with API-level reset",
                       add_help=False)
    s.add_argument("rest", nargs="*")
    s = sub.add_parser("serve", help="run the platform web server (settings come from KOPS_* variables)")
    s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=8080)
    a = ap.parse_args(argv)

    def sdir(x: str) -> Path:
        p = Path(x)
        return p if p.exists() else config.SCENARIOS_DIR / x

    if a.cmd == "lint":
        from .lint import lint_scenario
        problems = lint_scenario(sdir(a.scenario))
        print("\n".join(problems) or "lint clean")
        return 1 if problems else 0
    if a.cmd == "selftest":
        from .selftest import selftest
        ok, rows = selftest(sdir(a.scenario), a.seed, a.repeats, a.jobs)
        for r in rows:
            mark = "ok " if r["outcome"] == r["expected"] and r["clean_reset"] else "BAD"
            print(f"[{mark}] {r['check']:<34} expected={r['expected']:<5} got={r['outcome']:<8} "
                  f"clean_reset={r['clean_reset']} {r['seconds']}s")
            if mark == "BAD":
                print("      ", json.dumps({"reason": r["reason"], "criteria": r["criteria"]}))
        print("SELFTEST", "PASSED" if ok else "FAILED")
        return 0 if ok else 1
    if a.cmd == "run":
        from .experiment import compare, run_experiment
        out = run_experiment(Path(a.experiment), a.jobs)
        print(compare(out))
        return 0
    if a.cmd == "lab":
        from . import lab
        if a.action == "up":
            print(lab.up(sdir(a.scenario), a.seed))
            return 0
        if a.action == "verify":
            return lab.verify(sdir(a.scenario), a.wait)
        if a.action == "task":
            print(lab.task(sdir(a.scenario)))
            return 0
        lab.down(sdir(a.scenario))
        return 0
    if a.cmd == "selftest-vm":
        from .vmselftest import main as vm_main
        return vm_main(a.rest)
    if a.cmd == "serve":
        return _serve(a.host, a.port)
    if a.cmd == "compare":
        from .experiment import compare
        print(compare(Path(a.results_dir)))
        return 0
    return 2


def _serve(host: str, port: int) -> int:
    import uvicorn

    from .platform import Settings, create_app
    from .platform.provider import make_provider
    settings = Settings.from_env()
    app = create_app(settings, make_provider(settings))
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
