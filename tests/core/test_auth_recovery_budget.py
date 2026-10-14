"""Bound repeated automatic browser recovery without blocking explicit refresh."""
from __future__ import annotations

from notebooklm_tools.core import auth_recovery_budget as budget


def test_cooldown_failure_cap_and_new_revision(monkeypatch):
    budget._budgets.clear()
    now = [1000.0]
    monkeypatch.setattr(budget.time, "monotonic", lambda: now[0])
    monkeypatch.setenv("NOTEBOOKLM_AUTH_RECOVERY_COOLDOWN_SECONDS", "30")
    monkeypatch.setenv("NOTEBOOKLM_AUTH_MAX_HEADLESS_FAILURES", "2")

    assert budget.allow_automatic_recovery("alpha", "rev1")
    budget.finish_automatic_recovery("alpha", False)
    assert not budget.allow_automatic_recovery("alpha", "rev1")
    now[0] += 31
    assert budget.allow_automatic_recovery("alpha", "rev1")
    budget.finish_automatic_recovery("alpha", False)
    now[0] += 31
    assert not budget.allow_automatic_recovery("alpha", "rev1")
    assert budget.allow_automatic_recovery("alpha", "rev2")


def test_profile_budget_is_isolated_and_success_resets_failures(monkeypatch):
    budget._budgets.clear()
    now = [100.0]
    monkeypatch.setattr(budget.time, "monotonic", lambda: now[0])
    monkeypatch.setenv("NOTEBOOKLM_AUTH_RECOVERY_COOLDOWN_SECONDS", "0")
    monkeypatch.setenv("NOTEBOOKLM_AUTH_MAX_HEADLESS_FAILURES", "1")

    assert budget.allow_automatic_recovery("alpha", None)
    budget.finish_automatic_recovery("alpha", False)
    assert not budget.allow_automatic_recovery("alpha", None)
    assert budget.allow_automatic_recovery("beta", None)
    budget.finish_automatic_recovery("beta", True)
    assert budget.allow_automatic_recovery("beta", None)


def test_invalid_environment_values_use_safe_defaults(monkeypatch):
    budget._budgets.clear()
    monkeypatch.setenv("NOTEBOOKLM_AUTH_RECOVERY_COOLDOWN_SECONDS", "not-a-number")
    monkeypatch.setenv("NOTEBOOKLM_AUTH_MAX_HEADLESS_FAILURES", "not-a-number")
    assert budget.allow_automatic_recovery("alpha", None)
    budget.finish_automatic_recovery("alpha", False)
    assert not budget.allow_automatic_recovery("alpha", None)
