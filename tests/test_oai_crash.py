"""OpenAI Agents SDK RunState detector. Expected statuses observed in real runs (openai-agents 0.24.0, offline scripted model)."""
import json
import pytest
agents = pytest.importorskip("agents", reason="openai-agents extra missing: uv run --extra test pytest")
from agentsignal_check.detectors.oai_crash import run
EFF = ["tests.fixtures.payments:charge"]
CTX = {"order_id": "order-42"}
def by(rep): return {r["detector"]: r["status"] for r in rep["results"]}

def test_naive_agent_double_executes():
    s = by(run("tests.fixtures.oai_naive:build", EFF, CTX))
    assert s == {"baseline": "PASS", "double_execution.kill_resume": "FAIL",
                 "approval.lost_on_restart": "PASS", "approval.replay": "FAIL"}

def test_idempotent_agent_passes_everything():
    s = by(run("tests.fixtures.oai_idem:build", EFF, CTX))
    assert s == {"baseline": "PASS", "double_execution.kill_resume": "PASS",
                 "approval.lost_on_restart": "PASS", "approval.replay": "PASS"}

def test_cli_openai_agents(capsys):
    from agentsignal_check.cli import main
    assert main(["check", "--framework", "openai-agents", "--agent", "tests.fixtures.oai_naive:build",
                 "--effect", EFF[0], "--context", json.dumps(CTX), "--json"]) == 1
    rep = json.loads(capsys.readouterr().out)
    assert rep["framework"] == "openai-agents" and rep["env"]["packages"]["openai-agents"]
    assert main(["check", "--framework", "openai-agents", "--agent", "tests.fixtures.oai_idem:build",
                 "--effect", EFF[0], "--context", json.dumps(CTX)]) == 0
    assert "4/4 crash tests survived" in capsys.readouterr().out

def test_cli_openai_agents_missing_extra(monkeypatch, capsys):
    import builtins
    from agentsignal_check.cli import main
    real = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", lambda n, *a, **k: (_ for _ in ()).throw(ImportError(n)) if n == "agents" else real(n, *a, **k))
    assert main(["check", "--framework", "openai-agents", "--agent", "x:y", "--effect", "a:b"]) == 2
    assert "agentsignal-check[openai-agents]" in capsys.readouterr().err
