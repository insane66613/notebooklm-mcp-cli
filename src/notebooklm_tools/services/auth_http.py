"""HTTP-only renewal of eligible cookies and NotebookLM page tokens.

This does not renew Google's browser-dependent PSIDTS family and is not a
substitute for interactive login. No browser process is launched.
"""

from __future__ import annotations

import time

from notebooklm_tools.core.auth import AuthTokens, load_cached_tokens, save_tokens_to_cache
from notebooklm_tools.core.client import NotebookLMClient


def refresh_auth_http_only(profile_name: str) -> AuthTokens:
    """Refresh and validate one profile without opening a browser.

    Candidate credentials are not written until a real authenticated NotebookLM
    RPC succeeds. Any failed probe leaves the existing saved profile unchanged.
    """
    cached = load_cached_tokens(profile_name=profile_name)
    if cached is None or not cached.cookies:
        raise ValueError(f"No saved authentication for profile '{profile_name}'")

    with NotebookLMClient(
        cookies=cached.cookies,
        csrf_token=cached.csrf_token or "",
        session_id=cached.session_id or "",
        build_label=cached.build_label or "",
        base_host=cached.base_host or "",
        profile_name=profile_name,
        is_env_auth=True,
    ) as client:
        client._refresh_auth_tokens()
        client.list_notebooks()
        refreshed = AuthTokens(
            cookies=client.cookies,
            csrf_token=client.csrf_token,
            session_id=client._session_id,
            build_label=client._bl,
            base_host=client._base_host,
            extracted_at=time.time(),
        )

    refreshed.revision = save_tokens_to_cache(
        refreshed,
        profile_name=profile_name,
        expected_revision=cached.revision,
        force=False,
    )
    return refreshed
