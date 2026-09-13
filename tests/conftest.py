"""Shared test fixtures."""

import os

import pytest

from notebooklm_tools.core.cookie_rotation import DISABLE_ROTATE_COOKIES_ENV


def pytest_collection_modifyitems(config, items):
    """Skip live E2E tests unless they were explicitly enabled."""
    if os.environ.get("NOTEBOOKLM_E2E"):
        return

    skip_e2e = pytest.mark.skip(reason="requires NOTEBOOKLM_E2E=1")
    for item in items:
        if item.get_closest_marker("e2e"):
            item.add_marker(skip_e2e)


@pytest.fixture(autouse=True)
def _isolate_storage(monkeypatch, tmp_path, request):
    """Point storage at a per-test temp dir without importing real legacy auth.

    Several code paths (e.g. BaseClient._update_cached_tokens, headless auth)
    write to the real auth cache and Chrome profile. Without this guard, tests
    that exercise them corrupt the developer's real login (see
    test_refresh_auth_tokens_success, which used to overwrite auth.json with
    fake test tokens).

    Explicitly enabled E2E tests need the real authenticated profile. All other
    tests must also disable automatic migration sources; otherwise an empty
    pytest storage directory can copy real legacy auth and Chrome profile data
    into the temporary tree and accidentally reach live browser auth.
    """
    if os.environ.get("NOTEBOOKLM_E2E") and request.node.get_closest_marker("e2e"):
        return

    monkeypatch.setenv("NOTEBOOKLM_MCP_CLI_PATH", str(tmp_path / "storage"))

    from notebooklm_tools.utils import config as config_module

    monkeypatch.setattr(config_module, "OLD_CHROME_PROFILES", [])
    monkeypatch.setattr(config_module, "OLD_AUTH_LOCATIONS", [])
    monkeypatch.setattr(config_module, "OLD_ALIAS_LOCATIONS", [])


@pytest.fixture(autouse=True)
def _disable_cookie_rotation(monkeypatch):
    """Keep tests from hitting accounts.google.com.

    BaseClient._call_rpc rotates Google cookies before real RPC calls; a test
    with a mocked HTTP client could otherwise "succeed" at rotation against
    the mock. Tests that exercise rotation itself re-enable it with
    monkeypatch.delenv.
    """
    monkeypatch.setenv(DISABLE_ROTATE_COOKIES_ENV, "1")
