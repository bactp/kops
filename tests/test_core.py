import json
import subprocess
from pathlib import Path

import pytest

from kops.gateway import BudgetExhausted, Gateway, Trace, classify_command
from kops.harness import ShellLoopAgent, parse_reply
from kops.models import ScriptedModel
from kops.recorder import auto_failure_labels, derive_metrics
from kops.scenario import ScenarioError, load_scenario, make_params, render
from kops.verifier import FAIL, PASS, Verifier

S03 = Path(__file__).resolve().parents[1] / "scenarios" / "kops-net-service-endpoint-repair-001"


def fake_run(table):
    """Gateway run_cmd stub: table maps a joined argv suffix to (rc, out, err)."""
    def run(argv, env, timeout):
        key = " ".join(argv[1:])
        rc, out, err = table.get(key, (0, "", ""))
        return subprocess.CompletedProcess(argv, rc, out, err)
    return run


def gw(table=None, **kw):
    return Gateway(Path("/nonexistent"), Trace(), max_steps=kw.get("max_steps", 10),
                   max_wall_s=60, per_action_timeout_s=5, run_cmd=fake_run(table or {}))


# -- scenario ---------------------------------------------------------------
def test_params_deterministic_per_seed():
    spec = load_scenario(S03, 7).raw["task"]["parameters"]
    assert make_params(spec, 7) == make_params(spec, 7)
    assert make_params(spec, 7) != make_params(spec, 8)


def test_render_unknown_param_fails():
    with pytest.raises(ScenarioError):
        render("{{nope}}", {})


def test_agent_view_hides_hidden_content():
    scn = load_scenario(S03, 1)
    view = scn.agent_view()
    assert scn.params["ns"] in view and scn.params["app"] in view
    for hidden in ("criteria", "tier=frontend", "targetPort", "solution", "wrong_selector"):
        assert hidden not in view


def test_digest_changes_with_content(tmp_path):
    import shutil
    d = tmp_path / "s"
    shutil.copytree(S03, d)
    before = load_scenario(d, 1).digest
    (d / "reference" / "solution.sh").write_text("# changed\n")
    assert load_scenario(d, 1).digest != before


def test_reference_commands_render_and_parse():
    scn = load_scenario(S03, 1)
    cmds = scn.reference_commands()
    assert all(c.startswith("kubectl") for c in cmds)
    patch = [c for c in cmds if " patch " in c][0]
    import shlex
    body = json.loads(shlex.split(patch)[-1])
    assert body["spec"]["ports"][0]["targetPort"] == scn.params["port"]


# -- gateway -----------------------------------------------------------------
def test_non_kubectl_rejected_but_counts_a_step():
    g = gw()
    obs = g.run("ls -la")
    assert obs.kind == "policy_rejected" and g.steps == 1
    assert g.trace.events[0]["invalid"] is True


@pytest.mark.parametrize("cmd", ["kubectl get pods | grep x", "kubectl get pods && ls",
                                 "kubectl get pods --kubeconfig=/etc/x", "kubectl -s https://h get pods"])
def test_shell_syntax_and_forbidden_flags_rejected(cmd):
    assert gw().run(cmd).kind == "policy_rejected"


def test_exec_error_classification():
    g = gw({"get podz": (1, "", 'error: the server doesn\'t have a resource type "podz"'),
            "get pod nope": (1, "", 'Error from server (NotFound): pods "nope" not found')})
    assert g.run("kubectl get podz").kind == "exec_error"
    ev = g.trace.events
    assert ev[0]["invalid"] is True          # syntax-class error
    g.run("kubectl get pod nope")
    assert ev[1]["invalid"] is False         # NotFound is a legitimate observation


def test_mutation_detection():
    assert classify_command(["patch", "svc", "x"]) == (True, False)
    assert classify_command(["get", "pods"]) == (False, False)
    assert classify_command(["apply", "-f", "x", "--dry-run=client"]) == (False, True)
    assert classify_command(["rollout", "undo", "deploy/x"])[0] is True
    assert classify_command(["rollout", "status", "deploy/x"])[0] is False


def test_verb_not_confused_with_flag_values():
    # regression: `-n <ns> patch ...` was classified by the namespace value
    assert classify_command(["-n", "shop-ab12", "patch", "service", "x"])[0] is True
    assert classify_command(["-n", "shop-ab12", "get", "pods"])[0] is False
    assert classify_command(["--namespace=x", "delete", "pod", "p"])[0] is True


def test_step_budget_enforced():
    g = gw(max_steps=2)
    g.run("kubectl get pods"); g.run("kubectl get pods")
    with pytest.raises(BudgetExhausted) as e:
        g.run("kubectl get pods")
    assert e.value.reason == "steps"


def test_output_truncation_recorded():
    g = Gateway(Path("/x"), Trace(), max_steps=3, max_wall_s=60, per_action_timeout_s=5,
                max_output_bytes=10, run_cmd=fake_run({"get pods": (0, "x" * 100, "")}))
    obs = g.run("kubectl get pods")
    assert obs.truncated and len(obs.stdout) == 10


# -- harness -----------------------------------------------------------------
def test_parse_reply():
    assert parse_reply("```bash\nkubectl get pods\n```") == ("command", "kubectl get pods")
    assert parse_reply("done\nSUBMIT: fixed it")[0] == "submit"
    assert parse_reply("I think the service is wrong")[0] == "malformed"
    assert parse_reply("```bash\nkubectl get a\nkubectl get b\n```")[0] == "malformed"


def test_loop_records_parse_error_error_and_recovery():
    model = ScriptedModel([
        "no idea",                                           # malformed
        "```bash\nkubectl get podz\n```",                    # invalid exec_error
        "```bash\nkubectl get pods\n```",                    # ok (recovery)
        "```bash\nkubectl patch svc a -p x\n```",            # mutating ok
        "SUBMIT: fixed",
    ])
    g = gw({"get podz": (1, "", "error: the server doesn't have a resource type \"podz\"")})
    out = ShellLoopAgent("t", model).run("task", g)
    assert out.termination == "submitted" and out.claim == "fixed"
    m = derive_metrics(g.trace.events, 1.0)
    assert (m["steps"], m["parse_errors"], m["exec_errors"], m["invalid_actions"]) == (4, 1, 1, 2)
    assert m["mutating_steps"] == 1 and m["had_error"] and m["recovery_count"] == 1  # error->ok transitions; a streak counts once
    assert m["executable_command_rate"] == 0.5


def test_loop_budget_exhaustion():
    out = ShellLoopAgent("t", ScriptedModel(["```bash\nkubectl get pods\n```"])).run("task", gw(max_steps=3))
    assert out.termination == "budget_steps"


def test_auto_labels_only_for_fail():
    m = derive_metrics([], 0)
    assert auto_failure_labels("PASS", m, "submitted") == []
    assert "no_attempt" in auto_failure_labels("FAIL", m, "no_action")


# -- verifier (fake cluster) ----------------------------------------------------
class FakeCluster:
    def __init__(self, objs):
        self.objs = objs

    def kubectl(self, *args, **kw):
        args = list(args)
        key = " ".join(a for a in args if a not in ("-o", "json"))
        if key in self.objs:
            return subprocess.CompletedProcess(args, 0, json.dumps(self.objs[key]), "")
        return subprocess.CompletedProcess(args, 1, "", 'Error from server (NotFound): not found')


def crit(**check):
    return {"id": "c", "invariant": "i", "required": True, "check": check}


def test_unchanged_guard_detects_change():
    obj = {"spec": {"template": {"x": 1}}}
    fc = FakeCluster({"-n n get deployment d": obj})
    v = Verifier(fc, [crit(type="k8s.unchanged", resource={"kind": "Deployment", "name": "d", "namespace": "n"},
                           jsonpaths=[".spec.template"])])
    v.capture_baselines()
    assert v.evaluate(settle=False)[0].status == PASS
    obj["spec"]["template"]["x"] = 2
    assert v.evaluate(settle=False)[0].status == FAIL


def test_unchanged_guard_fails_when_resource_deleted():
    fc = FakeCluster({"-n n get service s": {"metadata": {"uid": "1"}}})
    v = Verifier(fc, [crit(type="k8s.unchanged", resource={"kind": "Service", "name": "s", "namespace": "n"},
                           jsonpaths=[".metadata.uid"])])
    v.capture_baselines()
    fc.objs.clear()
    assert v.evaluate(settle=False)[0].status == FAIL


def test_endpoints_check_counts_ready_on_port():
    sl = {"items": [{"ports": [{"port": 8080}], "endpoints": [
        {"conditions": {"ready": True}}, {"conditions": {"ready": True}}, {"conditions": {"ready": False}}]}]}
    fc = FakeCluster({"-n n get endpointslices -l kubernetes.io/service-name=s": sl})
    c = crit(type="k8s.endpoints", service="s", namespace="n", min_ready=2, port=8080)
    assert Verifier(fc, [c]).evaluate(settle=False)[0].status == PASS
    c2 = crit(type="k8s.endpoints", service="s", namespace="n", min_ready=2, port=80)
    assert Verifier(fc, [c2]).evaluate(settle=False)[0].status == FAIL


def test_verifier_error_makes_trial_invalid_not_fail():
    v = Verifier(FakeCluster({}), [crit(type="nonexistent.check")])
    res = v.evaluate(settle=False)
    assert res[0].status == "error" and Verifier.outcome(res) == "INVALID"


def test_outcome_all_required():
    from kops.verifier import CriterionResult as R
    ok, bad = R("a", "a", True, PASS, ""), R("b", "b", True, FAIL, "")
    assert Verifier.outcome([ok, ok]) == "PASS" and Verifier.outcome([ok, bad]) == "FAIL"
    assert Verifier.outcome([ok, R("c", "c", False, FAIL, "")]) == "PASS"


def test_scenario_lints_clean():
    from kops.lint import lint_scenario
    assert lint_scenario(S03) == []
