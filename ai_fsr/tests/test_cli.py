"""Unit tests for the CLI module."""

from unittest.mock import patch

from typer.testing import CliRunner

from ai_fsr.cli import app

runner = CliRunner()


class TestCLIBasic:
    """Tests for basic CLI functionality."""

    def test_help_command(self):
        """The --help flag should display help text and exit 0."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ai-fsr" in result.output.lower() or "init" in result.output.lower()

    def test_version_flag(self):
        """The --version flag should show the version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_no_args_shows_help(self):
        """Running with no arguments should not crash."""
        result = runner.invoke(app, [])
        # Typer typically exits 0 or 2 when no args given
        assert result.exit_code in (0, 2)


class TestInitCommand:
    """Tests for the init command."""

    def test_init_help(self):
        """The init --help should display init-specific help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0

    @patch("ai_fsr.cli.init_project")
    def test_init_calls_init_project(self, mock_init):
        """The init command should call init_project with the project name."""
        runner.invoke(app, ["init", "my-test-project"])
        mock_init.assert_called_once()

    @patch("ai_fsr.cli.init_project")
    def test_init_with_invalid_name(self, mock_init):
        """The init command should handle invalid project names."""
        mock_init.side_effect = ValueError("Invalid project name")
        result = runner.invoke(app, ["init", ""])
        assert result.exit_code != 0
