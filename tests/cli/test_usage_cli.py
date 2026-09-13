"""Tests for profile-aware plan usage CLI selection."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from notebooklm_tools.cli.main import app

runner = CliRunner()
_USAGE_RESULT = {
    "windows": [
        {
            "window": "rolling",
            "percent_used": 10.0,
            "percent_remaining": 90.0,
            "resets_at": None,
        }
    ],
    "tier": None,
}


def test_usage_accepts_long_profile_option():
    client = MagicMock()
    with (
        patch("notebooklm_tools.cli.commands.usage.get_client", return_value=client) as get_client,
        patch("notebooklm_tools.cli.commands.usage.usage_service.get_usage", return_value=_USAGE_RESULT),
    ):
        result = runner.invoke(app, ["usage", "--profile", "work", "--json"])

    assert result.exit_code == 0
    get_client.assert_called_once_with("work")


def test_usage_accepts_short_profile_option():
    client = MagicMock()
    with (
        patch("notebooklm_tools.cli.commands.usage.get_client", return_value=client) as get_client,
        patch("notebooklm_tools.cli.commands.usage.usage_service.get_usage", return_value=_USAGE_RESULT),
    ):
        result = runner.invoke(app, ["usage", "-p", "personal", "--json"])

    assert result.exit_code == 0
    get_client.assert_called_once_with("personal")


def test_usage_without_profile_preserves_default_client_behavior():
    client = MagicMock()
    with (
        patch("notebooklm_tools.cli.commands.usage.get_client", return_value=client) as get_client,
        patch("notebooklm_tools.cli.commands.usage.usage_service.get_usage", return_value=_USAGE_RESULT),
    ):
        result = runner.invoke(app, ["usage", "--json"])

    assert result.exit_code == 0
    get_client.assert_called_once_with()


def test_usage_missing_profile_value_is_cli_error():
    result = runner.invoke(app, ["usage", "--profile"])

    assert result.exit_code != 0
