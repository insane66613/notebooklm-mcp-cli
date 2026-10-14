"""HTTP-only refresh never launches a browser and never persists unvalidated cookies."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from notebooklm_tools.services import auth_http


def _cached():
    return SimpleNamespace(
        cookies={"SID": "old"},
        csrf_token="old",
        session_id="old-sid",
        build_label="old-bl",
        base_host="notebooklm.google.com",
        revision=None,
    )


class FakeClient:
    fail = False

    def __init__(self, **kwargs):
        self.profile_name = kwargs["profile_name"]
        self.is_env_auth = kwargs["is_env_auth"]
        self.cookies = {"SID": "new"}
        self.csrf_token = "new-csrf"
        self._session_id = "new-sid"
        self._bl = "new-bl"
        self._base_host = "notebooklm.google.com"

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def _refresh_auth_tokens(self):
        if self.fail:
            raise ValueError("Google redirected to login")

    def list_notebooks(self):
        return []


def test_http_refresh_validates_before_persist(monkeypatch):
    saved = Mock(return_value="rev-new")
    monkeypatch.setattr(auth_http, "load_cached_tokens", lambda **_: _cached())
    monkeypatch.setattr(auth_http, "save_tokens_to_cache", saved)
    monkeypatch.setattr(auth_http, "NotebookLMClient", FakeClient)
    refreshed = auth_http.refresh_auth_http_only("secondary")
    assert refreshed.csrf_token == "new-csrf"
    assert refreshed.revision == "rev-new"
    assert saved.call_args.kwargs["profile_name"] == "secondary"
    assert saved.call_args.kwargs["force"] is False


def test_http_refresh_never_persists_rejected_credentials(monkeypatch):
    class RejectedClient(FakeClient):
        fail = True

    saved = Mock()
    monkeypatch.setattr(auth_http, "load_cached_tokens", lambda **_: _cached())
    monkeypatch.setattr(auth_http, "save_tokens_to_cache", saved)
    monkeypatch.setattr(auth_http, "NotebookLMClient", RejectedClient)
    with pytest.raises(ValueError, match="redirected"):
        auth_http.refresh_auth_http_only("secondary")
    saved.assert_not_called()


def test_http_refresh_requires_saved_profile(monkeypatch):
    monkeypatch.setattr(auth_http, "load_cached_tokens", lambda **_: None)
    with pytest.raises(ValueError, match="No saved"):
        auth_http.refresh_auth_http_only("missing")
