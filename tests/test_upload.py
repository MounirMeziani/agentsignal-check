"""--upload against a local mock HTTP server (no network)."""
import io, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytest
from agentsignal_check import upload as up

REPORT = {"framework": "langgraph", "results": [{"detector": "baseline", "status": "FAIL", "detail": "x"}]}
FAKE_KEY = "as_live_testkey_not_real"


class Mock:
    def __init__(self, status=201, body=None, headers=None):
        self.status, self.body, self.headers, self.seen = status, body, headers or {}, []
        mock = self
        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                mock.seen.append({"path": self.path, "auth": self.headers.get("Authorization"),
                                  "ctype": self.headers.get("Content-Type"),
                                  "body": json.loads(self.rfile.read(n))})
                payload = json.dumps(mock.body if mock.body is not None else {}).encode()
                self.send_response(mock.status)
                for k, v in mock.headers.items():
                    self.send_header(k, v)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers(); self.wfile.write(payload)
            def log_message(self, *a): pass
        self.srv = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_port}/api/check/runs"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
    def close(self): self.srv.shutdown(); self.srv.server_close()


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("AGENTSIGNAL_API_KEY", FAKE_KEY)
    return monkeypatch


def run_up(mock, env):
    env.setenv("AGENTSIGNAL_API_URL", mock.url)
    out = io.StringIO()
    try:
        res = up.upload(REPORT, out=out, timeout=5)
    finally:
        mock.close()
    return res, out.getvalue()


def test_success_prints_run_id_and_fix_links(env):
    m = Mock(201, {"run_id": "run_123", "fix_links": [
        {"detector": "baseline", "url": "https://tryagentsignal.com/fix/baseline"},
        "https://tryagentsignal.com/fix/x"]})
    (ok, rid), out = run_up(m, env)
    assert ok and rid == "run_123"
    assert "run_123" in out and "https://tryagentsignal.com/fix/baseline" in out and "fix/x" in out
    assert m.seen[0]["auth"] == f"Bearer {FAKE_KEY}"
    assert m.seen[0]["ctype"] == "application/json" and m.seen[0]["body"] == REPORT
    assert m.seen[0]["path"] == "/api/check/runs"
    assert FAKE_KEY not in out


@pytest.mark.parametrize("code,needle", [(401, "invalid or revoked"), (413, "too large"),
                                         (429, "rate limit"), (500, "HTTP 500")])
def test_http_errors(env, code, needle):
    m = Mock(code, {"error": "x"}, {"Retry-After": "120"} if code == 429 else None)
    (ok, why), out = run_up(m, env)
    assert not ok and why == f"http-{code}" and needle in out and FAKE_KEY not in out
    if code == 429:
        assert "Retry-After: 120s" in out


def test_network_error(env):
    env.setenv("AGENTSIGNAL_API_URL", "http://127.0.0.1:9/api/check/runs")  # discard port, refused
    out = io.StringIO()
    ok, why = up.upload(REPORT, out=out, timeout=3)
    assert not ok and why == "network" and "network error" in out.getvalue()


def test_no_key_hint(monkeypatch):
    monkeypatch.delenv("AGENTSIGNAL_API_KEY", raising=False)
    out = io.StringIO()
    assert up.upload(REPORT, out=out) == (False, "no-key")
    assert out.getvalue().strip() == up.NO_KEY_HINT and out.getvalue().count("\n") == 1


def test_client_side_size_cap(env):
    env.setenv("AGENTSIGNAL_API_URL", "http://127.0.0.1:9/x")
    out = io.StringIO()
    ok, why = up.upload({"blob": "a" * (300 * 1024)}, out=out)
    assert not ok and why == "too-large"


# ---- CLI wiring (needs the langgraph extra; skipped otherwise via importorskip) ----
EFF = "tests.fixtures.payments:charge"

def _cli(args, capsys):
    pytest.importorskip("langgraph.checkpoint.sqlite")
    from agentsignal_check.cli import main
    code = main(["check", "--effect", EFF, "--input", '{"amount":5}', "--json"] + args)
    return code, capsys.readouterr()


def test_cli_no_key_without_upload_is_unchanged(monkeypatch, capsys):
    monkeypatch.delenv("AGENTSIGNAL_API_KEY", raising=False)
    code, cap = _cli(["--graph", "tests.fixtures.idem_graph:build"], capsys)
    assert code == 0 and cap.err == "" and json.loads(cap.out)["results"]


def test_cli_no_key_with_upload_one_line_hint(monkeypatch, capsys):
    monkeypatch.delenv("AGENTSIGNAL_API_KEY", raising=False)
    code, cap = _cli(["--graph", "tests.fixtures.idem_graph:build", "--upload"], capsys)
    assert code == 0 and cap.err == up.NO_KEY_HINT + "\n"
    json.loads(cap.out)  # stdout stays pure JSON


def test_cli_upload_failure_keeps_exit_code(env, capsys):
    m = Mock(401, {"error": "bad key"}); env.setenv("AGENTSIGNAL_API_URL", m.url)
    try:
        code, cap = _cli(["--graph", "tests.fixtures.idem_graph:build", "--upload"], capsys)
        code_n, _ = _cli(["--graph", "tests.fixtures.naive_graph:build", "--upload"], capsys)
    finally:
        m.close()
    assert code == 0 and code_n == 1 and "401" in cap.err
    json.loads(cap.out)


def test_cli_upload_strict_fails_on_upload_error(env, capsys):
    m = Mock(429, {}); env.setenv("AGENTSIGNAL_API_URL", m.url)
    try:
        code, cap = _cli(["--graph", "tests.fixtures.idem_graph:build", "--upload", "--upload-strict"], capsys)
    finally:
        m.close()
    assert code == 3 and "rate limit" in cap.err


def test_cli_upload_success_posts_full_json(env, capsys):
    m = Mock(201, {"run_id": "run_9", "fix_links": []}); env.setenv("AGENTSIGNAL_API_URL", m.url)
    try:
        code, cap = _cli(["--graph", "tests.fixtures.naive_graph:build", "--upload"], capsys)
    finally:
        m.close()
    assert code == 1 and "run_9" in cap.err
    assert m.seen[0]["body"] == json.loads(cap.out)
