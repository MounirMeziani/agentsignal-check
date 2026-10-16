"""Versions/timestamp recorded with every run (read-only, via importlib.metadata)."""
import datetime, platform
from importlib import metadata

PKGS = ["langgraph", "langgraph-checkpoint", "langgraph-checkpoint-sqlite", "langchain-core", "openai-agents", "openai"]

def collect():
    def v(p):
        try: return metadata.version(p)
        except metadata.PackageNotFoundError: return None
    return {"agentsignal_check": v("agentsignal-check"),
            "python": platform.python_version(),
            "packages": {p: v(p) for p in PKGS if v(p)},
            "run_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}

def footer(env):
    if not env: return ""
    p = env.get("packages", {})
    parts = [f"LangGraph {p['langgraph']}" if p.get("langgraph") else None,
             f"checkpoint {p['langgraph-checkpoint']}" if p.get("langgraph-checkpoint") else None,
             f"OpenAI Agents {p['openai-agents']}" if p.get("openai-agents") else None,
             f"Python {env.get('python')}", f"agentsignal-check {env.get('agentsignal_check')}", env.get("run_at")]
    return " · ".join(x for x in parts if x)
