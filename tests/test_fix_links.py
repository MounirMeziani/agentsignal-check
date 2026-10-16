import io, os, urllib.request
import pytest
from agentsignal_check.links import FIX_URLS, fix_url
from agentsignal_check import report as md, card

DETS = ["baseline", "double_execution.kill_resume", "double_execution.kill_before_checkpoint",
        "approval.lost_on_restart", "approval.replay"]
def rep(fw):
    return {"framework": fw, "results": [{"detector": d, "status": "FAIL", "detail": "x"} for d in DETS]}

def test_openai_agents_links_never_point_at_langgraph():
    for d in DETS:
        assert "/openai-agents-" in fix_url(d, "openai-agents") and "langgraph" not in fix_url(d, "openai-agents")
    assert fix_url("approval.lost_on_restart", "openai-agents").endswith("/openai-agents-approval-resume/")
    assert fix_url("approval.replay", "openai-agents").endswith("/openai-agents-idempotent-approval/")

def test_langgraph_links_unchanged_and_default():
    assert fix_url("approval.replay", "langgraph").endswith("/langgraph-approval-ui/")
    assert fix_url("approval.lost_on_restart", None) == fix_url("approval.lost_on_restart", "langgraph")
    assert fix_url("unknown.detector", "openai-agents").endswith("/templates/")

@pytest.mark.parametrize("fw", ["openai-agents", "langgraph"])
def test_every_renderer_uses_framework_links(fw):
    other = "langgraph-" if fw == "openai-agents" else "openai-agents-"
    out = md.render(rep(fw), "t")
    html = card.render_html(rep(fw), "t")
    buf = io.StringIO(); card.print_card(rep(fw), "t", file=buf)
    for text in (out, html, buf.getvalue()):
        assert other not in text
    assert all(fix_url(d, fw) in out and fix_url(d, fw) in html and fix_url(d, fw) in buf.getvalue() for d in DETS)

@pytest.mark.skipif(not os.environ.get("AGENTSIGNAL_NET_TESTS"), reason="set AGENTSIGNAL_NET_TESTS=1 to hit the network")
def test_all_fix_urls_return_200():
    for url in {u for m in FIX_URLS.values() for u in m.values()}:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "agentsignal-check-tests"}), timeout=20) as r:
            assert r.status == 200, url
