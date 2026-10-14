"""Bound automatic headless authentication attempts per saved profile.

Only automatic RPC recovery uses this budget. Explicit CLI/MCP refresh remains
available to callers, and a changed credential revision resets the budget.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass


@dataclass
class _Budget:
    revision: str | None
    last_attempt: float = float("-inf")
    failures: int = 0


_lock = threading.Lock()
_budgets: dict[str, _Budget] = {}


def _config_number(name: str, fallback: int) -> int:
    try:
        return max(0, int(os.environ.get(name, str(fallback))))
    except ValueError:
        return fallback


def allow_automatic_recovery(profile: str, revision: str | None) -> bool:
    """Reserve a bounded automatic attempt, or refuse without launching Chrome."""
    cooldown = _config_number("NOTEBOOKLM_AUTH_RECOVERY_COOLDOWN_SECONDS", 900)
    failure_limit = _config_number("NOTEBOOKLM_AUTH_MAX_HEADLESS_FAILURES", 3)
    now = time.monotonic()
    with _lock:
        budget = _budgets.get(profile)
        if budget is None or budget.revision != revision:
            budget = _Budget(revision=revision)
            _budgets[profile] = budget
        if failure_limit and budget.failures >= failure_limit:
            return False
        if now - budget.last_attempt < cooldown:
            return False
        budget.last_attempt = now
        return True


def finish_automatic_recovery(profile: str, success: bool) -> None:
    """Record the result; a successful recovery clears the failure count."""
    with _lock:
        budget = _budgets.get(profile)
        if budget is None:
            return
        budget.failures = 0 if success else budget.failures + 1
