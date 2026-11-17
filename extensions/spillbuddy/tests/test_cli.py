"""Tests for SpillBuddy CLI."""

import pytest
from spillbuddy.cli import build_parser, format_result


class TestBuildParser:
    def test_lookup_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["lookup", "red wine", "cotton"])
        assert args.command == "lookup"
        assert args.stain == "red wine"
        assert args.fabric == "cotton"

    def test_list_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"

    def test_interactive_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["interactive"])
        assert args.command == "interactive"

    def test_version(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_no_args_shows_help(self):
        from spillbuddy.cli import main
        import sys
        old_argv = sys.argv
        sys.argv = ["spillbuddy"]
        with pytest.raises(SystemExit):
            main()
        sys.argv = old_argv


class TestFormatResult:
    def test_format_basic(self):
        result = {
            "stain": "red wine",
            "fabric": "cotton",
            "method": "Blot excess. Rinse with cold water.",
            "caution": "Do NOT use hot water.",
        }
        output = format_result(result)
        assert "SpillBuddy" in output
        assert "Red Wine" in output
        assert "Cotton" in output
        assert "Blot excess" in output
        assert "Do NOT" in output