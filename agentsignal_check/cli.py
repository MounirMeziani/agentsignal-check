"""agentsignal check — crash-test an agent for double execution / lost approvals."""
import argparse, json, sys
from .detectors import langgraph_crash

def main(argv=None):
    from . import __version__
    p = argparse.ArgumentParser(prog="agentsignal")
    p.add_argument("--version", action="version", version=f"agentsignal-check {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="run detectors against a target agent")
    c.add_argument("--version", action="version", version=f"agentsignal-check {__version__}")
    c.add_argument("--framework", default="langgraph", choices=["langgraph", "openai-agents"])
    c.add_argument("--graph", help="langgraph: module:factory; factory(checkpointer) -> compiled graph")
    c.add_argument("--agent", help="openai-agents: module:factory; factory() -> agents.Agent with needs_approval tools")
    c.add_argument("--context", default="{}", help="openai-agents: JSON run context (dict) passed to Runner.run")
    c.add_argument("--effect", action="append", required=True, help="module:function side effect to watch (repeatable)")
    c.add_argument("--input", default="{}", help="JSON input for the first invoke")
    c.add_argument("--resume", default="true", help="JSON value sent to every interrupt (auto-approve)")
    c.add_argument("--report", help="write a markdown report to this path")
    c.add_argument("--html", help="write a self-contained HTML report card")
    c.add_argument("--png", help="write a 1200x630 OG card PNG (needs the [png] extra)")
    c.add_argument("--svg", help="write the terminal report card as SVG (rich export)")
    c.add_argument("--badge", help="write a shields-style SVG badge here and print a README snippet")
    c.add_argument("--badge-link", default="report.html", help="URL the badge links to (your latest report)")
    c.add_argument("--json", action="store_true", help="machine-readable output")
    a = p.parse_args(argv)
    if a.framework == "openai-agents":
        if not a.agent:
            p.error("--framework openai-agents needs --agent module:factory")
        try:
            import agents  # noqa: F401
        except ImportError:
            print("agentsignal: OpenAI Agents SDK support not installed. Run:\n"
                  '  pip install "agentsignal-check[openai-agents]"', file=sys.stderr)
            return 2
        from .detectors import oai_crash
        report = oai_crash.run(a.agent, a.effect, json.loads(a.context))
        a.graph = a.agent
    else:
        if not a.graph:
            p.error("--framework langgraph needs --graph module:factory")
        try:
            import langgraph.checkpoint.sqlite  # noqa: F401
        except ImportError:
            print("agentsignal: LangGraph support not installed. Run:\n"
                  '  pip install "agentsignal-check[langgraph]"', file=sys.stderr)
            return 2
        report = langgraph_crash.run(a.graph, a.effect, json.loads(a.input), json.loads(a.resume))
    from .env import collect
    report["env"] = collect()
    if a.report:
        from .report import render
        open(a.report, "w").write(render(report, a.graph))
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        from .card import print_card
        print_card(report, a.graph)
    from . import card
    if a.html:
        import datetime
        open(a.html, "w").write(card.render_html(report, a.graph))
    if a.svg:
        card.export_svg(report, a.graph, a.svg)
    if a.png:
        card.render_png(report, a.graph, a.png)
    if a.badge:
        svg, md = card.render_badge(report, a.badge_link)
        open(a.badge, "w").write(svg)
        md = md.replace("agentsignal-badge.svg", a.badge)
        print(md, file=sys.stderr if a.json else sys.stdout)
    return 1 if any(r["status"] == "FAIL" for r in report["results"]) else 0

if __name__ == "__main__":
    sys.exit(main())
