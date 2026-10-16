"""--upload: POST the --json report to Agent Signal (Pro). Stdlib only."""
import json, os, sys, urllib.request, urllib.error

DEFAULT_URL = "https://tryagentsignal.com/api/check/runs"
MAX_BYTES = 256 * 1024
NO_KEY_HINT = ("agentsignal: --upload skipped: AGENTSIGNAL_API_KEY is not set "
               "(create a key at https://tryagentsignal.com/pro/keys)")


def upload(report, out=sys.stderr, timeout=15):
    """Return (ok, message). Never raises; never prints the key."""
    key = os.environ.get("AGENTSIGNAL_API_KEY", "").strip()
    if not key:
        print(NO_KEY_HINT, file=out)
        return False, "no-key"
    url = os.environ.get("AGENTSIGNAL_API_URL", "").strip() or DEFAULT_URL
    body = json.dumps(report).encode()
    if len(body) > MAX_BYTES:
        print(f"agentsignal: upload failed: report is {len(body)} bytes, limit is {MAX_BYTES}", file=out)
        return False, "too-large"
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "User-Agent": "agentsignal-check"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        msgs = {401: "invalid or revoked API key (401). Check AGENTSIGNAL_API_KEY.",
                403: "this key has no Pro access (403).",
                413: "report too large for the server (413, limit 256 KB).",
                429: "rate limit hit (429, 60 uploads/hour per key). Try again later."}
        msg = msgs.get(e.code, f"server returned HTTP {e.code}.")
        if e.code == 429 and e.headers.get("Retry-After"):
            msg += f" Retry-After: {e.headers.get('Retry-After')}s."
        print(f"agentsignal: upload failed: {msg}", file=out)
        return False, f"http-{e.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        reason = getattr(e, "reason", e)
        print(f"agentsignal: upload failed: network error reaching {url}: {reason}", file=out)
        return False, "network"
    except ValueError:
        print("agentsignal: upload failed: server response was not JSON", file=out)
        return False, "bad-response"
    print(f"agentsignal: uploaded run {data.get('run_id', '?')}", file=out)
    links = data.get("fix_links") or []
    for l in links:
        if isinstance(l, dict):
            print(f"  fix: {l.get('detector', '')} {l.get('url', '')}".rstrip(), file=out)
        else:
            print(f"  fix: {l}", file=out)
    return True, data.get("run_id")
