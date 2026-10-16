# Changelog

## Unreleased
- **`--upload` (Signal Pro):** posts the `--json` report to `https://tryagentsignal.com/api/check/runs` with `Authorization: Bearer $AGENTSIGNAL_API_KEY` (override the URL with `AGENTSIGNAL_API_URL`) and prints the returned `run_id` and fix links. 401, 413, 429 and network errors print a clear message and never change the exit code; add `--upload-strict` to exit 3 when the upload fails on an otherwise passing run. With no key, `--upload` prints a one-line hint and the check runs exactly as before. With `--json`, upload messages go to stderr so stdout stays pure JSON.

## 0.3.0 (2026-10-16)
- **OpenAI Agents SDK:** `agentsignal check --framework openai-agents` with kill/resume, lost-approval, and replay detectors over `RunState.to_json()` / `RunState.from_json()`.
- New `[openai-agents]` extra (`openai-agents>=0.24`); `test` extra now pulls it in.
- Offline fixtures and pytest coverage for naive vs idempotent agents (`tests/fixtures/oai_*.py`, `tests/test_oai_crash.py`).
- README: install and run notes for the openai-agents path.

## 0.2.1 (2026-10-15)
- The card footer and HTML/OG tagline now read: "We kill your LangGraph agent mid-approval, restart it, and count how many times the tool ran."
- The badge reads "Crash-tested by Agent Signal | N/M" by default, and "Agent Signal crash test | passing" only when all detectors pass on the run.
- README: tagline under the screenshot, and badge docs.

## 0.2.0 (2026-10-15)
- **Report card:** a rich 80-column terminal card with the grade ("Approval flow: N/M crash tests survived"), double-charge and lost-approval risk, and one row per detector with why and a fix link. With `NO_COLOR` set or output piped, it prints plain text.
- **New outputs:** `--html` (a self-contained dark report page with OG/Twitter meta), `--svg` (terminal card export), `--png` (a 1200×630 OG card, needs the new `[png]` extra), and `--badge` with `--badge-link` (a static shields-style SVG and README snippet that says "passing" only when every detector passed, otherwise `N/M` in amber).
- **Env block:** `--json`, HTML and the card footer now record framework versions (langgraph, langgraph-checkpoint, …), the agentsignal-check version, the Python version and the run timestamp.
- **Clean-env testing:** a new `test` extra (`uv run --extra test pytest`). Without the LangGraph extra, the LangGraph tests are skipped with a clear message, and the CLI tells you what to install.
- `agentsignal check --version`.
- `rich` is now a runtime dependency.
- Honesty notes: under LangGraph's default async durability, some crash points are timing-dependent, so the safe example can show different results on different runs. The grades always reflect the actual run.

## 0.1.0 (2026-10-15)
- First release: `agentsignal check` with 5 LangGraph detectors (baseline, kill_resume, kill_before_checkpoint, lost_on_restart, replay), `--report` markdown and `--json`.
