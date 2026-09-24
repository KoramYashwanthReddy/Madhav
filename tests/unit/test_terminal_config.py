"""Unit tests verifying TerminalSettings configuration is properly loaded."""

import pytest

from max.config.sections import TerminalSettings
from max.config.settings import Settings, clear_settings_cache


@pytest.fixture(autouse=True)
def reset_cache():
    """Ensure settings cache is clean for each test."""
    clear_settings_cache()
    yield
    clear_settings_cache()


class TestTerminalSettingsDefaults:
    def test_terminal_settings_default_values(self):
        settings = TerminalSettings()
        assert settings.enabled is True
        assert settings.dry_run is False
        assert settings.default_shell == "POWERSHELL"
        assert settings.default_timeout == 30.0
        assert settings.max_output_bytes == 524288
        assert settings.allowed_working_directories == []
        assert settings.wsl_distribution is None
        assert settings.max_page_size == 100

    def test_terminal_settings_in_root_settings(self):
        settings = Settings()
        assert hasattr(settings, "terminal")
        assert isinstance(settings.terminal, TerminalSettings)

    def test_terminal_settings_enabled_by_default(self):
        settings = Settings()
        assert settings.terminal.enabled is True

    def test_terminal_settings_dry_run_false_by_default(self):
        settings = Settings()
        assert settings.terminal.dry_run is False

    def test_terminal_timeout_bounds(self):
        s = TerminalSettings(default_timeout=60.0)
        assert s.default_timeout == 60.0

    def test_terminal_dry_run_override(self):
        s = TerminalSettings(dry_run=True, enabled=False)
        assert s.dry_run is True
        assert s.enabled is False
