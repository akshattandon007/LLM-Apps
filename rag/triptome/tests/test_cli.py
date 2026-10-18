"""Tests for TripTome CLI commands."""

from click.testing import CliRunner
from triptome.cli import cli


def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "TripTome" in result.output


def test_cli_stats_empty():
    """Test stats on empty collection."""
    runner = CliRunner()
    result = runner.invoke(cli, ["stats"])
    assert result.exit_code == 0


def test_cli_ask_empty():
    """Test ask with no indexed documents."""
    runner = CliRunner()
    result = runner.invoke(cli, ["ask", "Where should I travel?"])
    assert result.exit_code == 0


def test_cli_version():
    """Test version output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "1.0.0" in result.output


def test_cli_clear_empty():
    """Test clear with empty collection."""
    runner = CliRunner()
    result = runner.invoke(cli, ["clear"], input="y\n")
    assert result.exit_code == 0