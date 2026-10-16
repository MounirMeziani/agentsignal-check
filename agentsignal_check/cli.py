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
        for r in report["results"]:
            print(f"[{r['status']}] {r['detector']}: {r['detail']}")
    return 1 if any(r["status"] == "FAIL" for r in report["results"]) else 0

if __name__ == "__main__":
    sys.exit(main())
