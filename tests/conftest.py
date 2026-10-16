import pytest
try:
    import langgraph.checkpoint.sqlite  # noqa: F401
    HAVE_LG = True
except ImportError:
    HAVE_LG = False

def pytest_collection_modifyitems(config, items):
    if HAVE_LG:
        return
    skip = pytest.mark.skip(reason='LangGraph extra missing: run `uv run --extra test pytest` '
                                   'or `pip install -e ".[test]"`')
    for it in items:
        if it.nodeid.startswith("tests/test_langgraph_crash.py") and "missing_extra" not in it.name:
            it.add_marker(skip)

def pytest_terminal_summary(terminalreporter):
    if not HAVE_LG:
        terminalreporter.write_line("NOTE: LangGraph tests skipped (extra not installed). "
                                    "Use: uv run --extra test pytest", yellow=True)
