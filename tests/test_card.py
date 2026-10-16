"""Report card / html / png / badge: honesty and degradation. No LangGraph needed."""
import io, json, os, subprocess, sys
from agentsignal_check import card

def rep(*statuses):
    names = ["baseline", "double_execution.kill_resume", "double_execution.kill_before_checkpoint",
             "approval.lost_on_restart", "approval.replay"]
    return {"framework": "langgraph", "results": [
        {"detector": n, "status": s, "detail": "crash after effect #1 -> re-executed {'tests.fixtures.payments:charge(1999,)[]': 3}" if s == "FAIL" else "ok"}
        for n, s in zip(names, statuses)]}

def test_grade_and_risk_come_from_results():
    s = card.summarize(rep("PASS", "FAIL", "PASS", "PASS", "FAIL"))
    assert (s["passed"], s["total"], s["all_pass"]) == (3, 5, False)
    assert s["double_risk"] == "HIGH" and s["lost_risk"] == "LOW"
    s = card.summarize(rep("PASS", "PASS", "WARN", "FAIL", "PASS"))
    assert s["double_risk"] == "UNKNOWN" and s["lost_risk"] == "HIGH" and s["passed"] == 3
    assert card.summarize(rep(*["PASS"] * 5))["all_pass"]

def test_short_detail_copies_real_count():
    assert "executed 3×" in card._short("crash after effect #1 -> re-executed {'tests.fixtures.payments:charge(1999,)[]': 3}")

def test_plain_output_when_not_tty_or_no_color(monkeypatch):
    buf = io.StringIO()  # StringIO.isatty() is False
    card.print_card(rep("PASS", "FAIL", "PASS", "PASS", "PASS"), "m:f", file=buf)
    out = buf.getvalue()
    assert "Approval flow: 4/5 crash tests survived" in out and "\x1b[" not in out and "╭" not in out
    assert "[FAIL] double_execution.kill_resume" in out and "fix: https://tryagentsignal.com/" in out

def test_rich_card_fits_80_cols(tmp_path):
    p = tmp_path / "c.svg"
    card.export_svg(rep("FAIL", "FAIL", "FAIL", "PASS", "FAIL"), "tests.fixtures.naive_graph:build", str(p))
    from rich.console import Console
    c = Console(record=True, width=80, file=io.StringIO(), force_terminal=True)
    c.print(card.build_renderable(rep("FAIL", "FAIL", "FAIL", "PASS", "FAIL"), "x:y"))
    txt = c.export_text()
    assert max(len(l) for l in txt.splitlines()) <= 80
    assert "1/5" in txt and p.read_text().startswith("<svg")

def test_html_self_contained_with_og():
    h = card.render_html(rep("PASS", "FAIL", "PASS", "PASS", "PASS"), "m:f")
    assert 'property="og:title"' in h and "twitter:card" in h and "4/5" in h
    assert "<script" not in h and "http://" not in h and '<link rel="stylesheet"' not in h
    assert '"Geist Mono"' in h and "ui-monospace" in h

def test_png_is_1200x630(tmp_path):
    from PIL import Image
    p = tmp_path / "og.png"; card.render_png(rep("PASS", "FAIL", "PASS", "PASS", "PASS"), "m:f", str(p))
    assert Image.open(p).size == (1200, 630)

def test_badge_passing_only_when_all_pass():
    svg, md = card.render_badge(rep(*["PASS"] * 5), "https://x/report")
    assert ">passing<" in svg and "5/5 passed" in md and "](https://x/report)" in md
    svg, md = card.render_badge(rep("PASS", "FAIL", "PASS", "PASS", "PASS"))
    assert "passing" not in svg and ">4/5<" in svg and "#dfb317" in svg and "4/5 passed" in md
    svg, _ = card.render_badge(rep(*["FAIL"] * 5))
    assert ">0/5<" in svg and "#dfb317" in svg

def test_json_output_unchanged_shape(monkeypatch, capsys):
    from agentsignal_check import cli
    fake = rep("PASS", "FAIL", "PASS", "PASS", "PASS")
    monkeypatch.setattr(cli.langgraph_crash, "run", lambda *a, **k: fake)
    import builtins; real = builtins.__import__
    assert cli.main(["check", "--graph", "m:f", "--effect", "a:b", "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    env = out.pop("env")
    assert out == {"framework": "langgraph", "results": fake["results"]}
    assert env["agentsignal_check"] and env["python"] and env["run_at"].endswith("Z")
    assert env["packages"].get("langgraph")

def test_env_in_html_and_card():
    from agentsignal_check.env import collect, footer
    r = rep(*["PASS"] * 5); r["env"] = collect()
    f = footer(r["env"]); assert f.startswith("LangGraph ") and "Python " in f
    assert f in card.render_html(r, "m:f")
    from rich.console import Console
    c = Console(record=True, width=80, file=io.StringIO(), force_terminal=True); c.print(card.build_renderable(r, "m:f"))
    t = c.export_text(); assert "LangGraph " + r["env"]["packages"]["langgraph"] in t
    assert max(len(l) for l in t.splitlines()) <= 80
