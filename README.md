# agentsignal check

Crash-test your AI agent for **double execution** and **lost approvals** before your users find them.
It runs on your machine or in CI. It's free and MIT-licensed. Built by [Agent Signal](https://tryagentsignal.com).

```bash
pip install "agentsignal-check[langgraph] @ git+https://github.com/MounirMeziani/agentsignal-check"

agentsignal check --graph myapp.graph:build --effect myapp.payments:charge \
  --input '{"amount":1999}' --report agentsignal-report.md
```

- `--graph mod:factory`: `factory(checkpointer)` returns your compiled LangGraph graph. The harness injects a SQLite checkpointer so state survives process death.
- `--effect mod:func` (can be repeated): the side effects that must happen at most once, such as a charge, an email or a delete.
- `--resume JSON`: the value sent to every `interrupt()`. Default `true` (approve).
- `--report FILE`: writes a markdown report with fixes. `--json` prints machine-readable output.
- Exit code 1 on any FAIL, so you can use it as a CI gate.

## Report card, HTML, OG image, badge
```bash
agentsignal check --graph myapp.graph:build --effect myapp.payments:charge \
  --html report.html --png og.png --badge agentsignal-badge.svg --badge-link https://example.com/report.html
```
- **Terminal:** an 80-column report card with the grade ("Approval flow: 3/5 crash tests survived"), double-charge and lost-approval risk, and one row per detector with why and how to fix. With `NO_COLOR` set or output piped, it prints plain text. `--json` output is unchanged.
- `--html`: a self-contained dark report page with OG/Twitter meta, and `--svg` exports the terminal card.
- `--png`: a 1200×630 OG card. It needs `pip install "agentsignal-check[png]"` (Pillow).
- `--badge`: a static SVG plus a README snippet. It says **passing** only when every detector passed on this run; otherwise it shows `N/M` in amber.

The grade, risks and badge are computed only from the detector results of the current run.

## Detectors (LangGraph)
| id | fault injected | FAIL means |
|---|---|---|
| `baseline` | none (clean run, auto-approve) | an effect ran twice with no crash (side effect before `interrupt()` in the same node) |
| `double_execution.kill_resume` | hard kill (`os._exit`) right after each effect, then resume in a fresh process | the effect was re-executed |
| `double_execution.kill_before_checkpoint` | hard kill before each checkpoint `put()`, after `put_writes` ([langgraph#8039](https://github.com/langchain-ai/langgraph/issues/8039)) | the effect was re-executed on recovery |
| `approval.lost_on_restart` | restart the process while paused | the pending approval is gone |
| `approval.replay` | deliver the same approval twice, including against a stale checkpoint | the effect ran again |

A duplicate means the same effect args returned **different** results. A retry that returns the same result (for example, a provider idempotency key) passes.

## Test scratch space
Each scenario sets `AS_SCENARIO` to a unique path. If your effect writes to a local store during the check, key the store on it so scenarios don't leak into each other.

## Fixing failures
Every FAIL in the report links to a free tested pattern on [tryagentsignal.com](https://tryagentsignal.com). Want it done for you? Use the [$79 Fix](https://tryagentsignal.com/fix).

## Develop / test
```bash
uv run --extra test pytest -q          # or: pip install -e ".[test]" && pytest -q
```
`test` installs pytest and the `langgraph` extra. If you run without it, the LangGraph tests are skipped with a note rather than failing with a cryptic error.
MIT © Mounir Meziani
