"""agentsignal check — crash-test an agent for double execution / lost approvals."""
import argparse, json, sys
from .detectors import langgraph_crash

def main(argv=None):
    from . import __version__
    p = argparse.ArgumentParser(prog="agentsignal")
    p.add_argument("--version", action="version", version=f"agentsignal-check {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="run detectors against a target agent")
    c.add_argument("--framework", default="langgraph", choices=["langgraph"])
    c.add_argument("--graph", required=True, help="module:factory; factory(checkpointer) -> compiled graph")
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
    try:
        import langgraph.checkpoint.sqlite  # noqa: F401
    except ImportError:
        print("agentsignal: LangGraph support not installed. Run:\n"
              '  pip install "agentsignal-check[langgraph]"', file=sys.stderr)
        return 2
    report = langgraph_crash.run(a.graph, a.effect, json.loads(a.input), json.loads(a.resume))
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
        open(a.html, "w").write(card.render_html(report, a.graph, datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")))
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
