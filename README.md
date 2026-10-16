# agentsignal check

Crash-test your AI agent for **double execution** and **lost approvals** before your users find them.
It runs on your machine or in CI. It's free and MIT-licensed. Built by [Agent Signal](https://tryagentsignal.com).

```bash
pip install "agentsignal-check[langgraph] @ git+https://github.com/MounirMeziani/agentsignal-check"
# or: pip install git+https://github.com/MounirMeziani/agentsignal-check  (then: pip install langgraph langgraph-checkpoint-sqlite)

agentsignal check --graph myapp.graph:build --effect myapp.payments:charge \
  --input '{"amount":1999}' --report agentsignal-report.md
```

- `--graph mod:factory`: `factory(checkpointer)` returns your compiled LangGraph graph. The harness injects a SQLite checkpointer so state survives process death.
- `--effect mod:func` (can be repeated): the side effects that must happen at most once, such as a charge, an email or a delete.
- `--resume JSON`: the value sent to every `interrupt()`. Default `true` (approve).
- `--report FILE`: writes a markdown report with fixes. `--json` prints machine-readable output.
- Exit code 1 on any FAIL, so you can use it as a CI gate.

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

## Develop
```bash
pip install -e '.[langgraph,dev]' && pytest -q
```
MIT © Mounir Meziani
