"""Runs without the langgraph extra."""
import subprocess, sys
def test_version():
    r = subprocess.run([sys.executable, "-m", "agentsignal_check.cli", "--version"], capture_output=True, text=True)
    from agentsignal_check import __version__
    assert r.returncode == 0 and __version__ in r.stdout
    r = subprocess.run([sys.executable, "-m", "agentsignal_check.cli", "check", "--version"], capture_output=True, text=True)
    assert r.returncode == 0 and __version__ in r.stdout
def test_report_render_no_langgraph():
    from agentsignal_check.report import render
    md = render({"framework": "langgraph", "results": [{"detector": "baseline", "status": "FAIL", "detail": "x"}]}, "m:f")
    assert "Verdict: **FAIL**" in md and "https://tryagentsignal.com/fix/" in md
