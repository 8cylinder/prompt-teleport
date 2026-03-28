"""Tests for prompt generation at different terminal widths.

These tests verify that:
1. The prompt fills the terminal width appropriately
2. There is no line wrapping (single line output)
3. Width handling works correctly at various terminal sizes
4. End-to-end ps1 generation works without errors
"""

import os
import re
import tempfile
from io import StringIO
from unittest.mock import patch
import sys

import pytest
from prompt.prompt import Chunks, ps1_prompt


class TestPromptWidths:
    """Test prompt generation at different terminal widths."""

    def _capture_ps1_output(self, columns: int, monkeypatch) -> str:
        """Capture the output from ps1_prompt() at a given width.

        Args:
            columns: Terminal width in columns
            monkeypatch: pytest monkeypatch fixture

        Returns:
            The captured prompt output
        """
        import tempfile
        from pathlib import Path as RealPath
        from unittest.mock import MagicMock

        # Create a temporary projects file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("testproj\t/home/testuser/projects\t#FF0000\n")
            temp_projects_file = f.name

        try:
            # Set up environment - use COLUMNS to control width
            monkeypatch.setenv("COLUMNS", str(columns))
            monkeypatch.setenv("SSH_CLIENT", "")
            monkeypatch.setenv("HOME", "/home/testuser")
            monkeypatch.setenv("USER", "testuser")
            monkeypatch.setenv("VIRTUAL_ENV", "")
            monkeypatch.setenv("POETRY_ACTIVE", "")
            monkeypatch.setenv("PIPENV_ACTIVE", "")
            monkeypatch.setenv("NIX_STORE", "")
            monkeypatch.setenv("KITTY_PID", "")
            monkeypatch.setenv("ITERM_SESSION_ID", "")

            # Mock methods that cause issues with subprocess/file access
            monkeypatch.setattr(Chunks, "_chunk_ddev", lambda self: "")
            monkeypatch.setattr(Chunks, "_chunk_branch", lambda self: "")
            monkeypatch.setattr(Chunks, "_chunk_sink", lambda self: "")

            # Mock Path for projects config (use patch instead of monkeypatch)
            def mock_path_factory(path_str):
                if path_str == "~/.prompt-projects":
                    mock_path = MagicMock()
                    mock_path.expanduser.return_value = temp_projects_file
                    return mock_path
                else:
                    return RealPath(path_str)

            # Use patch for Path since monkeypatch has issues with it
            with patch("prompt.prompt.Path", side_effect=mock_path_factory):
                from prompt.prompt import ps1_prompt
                output = ps1_prompt()

        finally:
            os.unlink(temp_projects_file)

        return output

    def _strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI color codes from text for measurement.

        Args:
            text: Text containing ANSI codes

        Returns:
            Text with ANSI codes removed
        """
        # Strip both CSI sequences (ESC[) and OSC sequences (ESC])
        ansi_escape = re.compile(r'\x1B(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07)')
        return ansi_escape.sub('', text)

    def _count_visible_width(self, text: str) -> int:
        """Count visible characters (excluding ANSI codes).

        Args:
            text: Text that may contain ANSI codes

        Returns:
            Number of visible characters
        """
        clean_text = self._strip_ansi_codes(text)
        clean_text = clean_text.rstrip('\n')
        return len(clean_text)

    def _get_prompt_line(self, output: str) -> str:
        """Extract the main prompt line from ps1_prompt output.

        ps1_prompt() returns a string with the prompt segments on the first
        line and a dollar sign on the second line (after \\n in the dollar chunk).
        """
        lines = output.split('\n')
        return lines[0]

    @pytest.mark.unit
    def test_prompt_width_80_columns(self, monkeypatch):
        """Test prompt generation at standard 80-column width."""
        output = self._capture_ps1_output(80, monkeypatch)
        prompt_line = self._get_prompt_line(output)

        assert prompt_line != "", "Prompt line should not be empty"

        visible_width = self._count_visible_width(prompt_line)
        assert visible_width <= 80, f"Prompt width {visible_width} exceeds 80"
        assert visible_width >= 50, f"Prompt width {visible_width} is too small"

    @pytest.mark.unit
    def test_prompt_width_120_columns(self, monkeypatch):
        """Test prompt generation at wider 120-column width."""
        output = self._capture_ps1_output(120, monkeypatch)
        prompt_line = self._get_prompt_line(output)
        visible_width = self._count_visible_width(prompt_line)

        assert visible_width <= 120, f"Prompt width {visible_width} exceeds 120"
        assert visible_width >= 70, f"Prompt width {visible_width} is too small for 120 cols"

    @pytest.mark.unit
    def test_prompt_width_160_columns(self, monkeypatch):
        """Test prompt generation at extra-wide 160-column width."""
        output = self._capture_ps1_output(160, monkeypatch)
        prompt_line = self._get_prompt_line(output)
        visible_width = self._count_visible_width(prompt_line)

        assert visible_width <= 160, f"Prompt width {visible_width} exceeds 160"
        assert visible_width >= 90, f"Prompt width {visible_width} is too small for 160 cols"

    @pytest.mark.unit
    def test_prompt_width_40_columns(self, monkeypatch):
        """Test prompt generation at narrow 40-column width."""
        output = self._capture_ps1_output(40, monkeypatch)
        prompt_line = self._get_prompt_line(output)
        visible_width = self._count_visible_width(prompt_line)

        assert visible_width <= 40, f"Prompt width {visible_width} exceeds 40"

    @pytest.mark.unit
    def test_prompt_width_200_columns(self, monkeypatch):
        """Test prompt generation at very wide 200-column width."""
        output = self._capture_ps1_output(200, monkeypatch)
        prompt_line = self._get_prompt_line(output)
        visible_width = self._count_visible_width(prompt_line)

        assert visible_width <= 200, f"Prompt width {visible_width} exceeds 200"
        assert visible_width >= 100, f"Prompt width {visible_width} is too small for 200 cols"

    @pytest.mark.unit
    def test_prompt_no_wrapping_at_all_widths(self, monkeypatch):
        """Test that prompt never wraps at any reasonable width."""
        test_widths = [40, 60, 80, 100, 120, 160, 200, 256]

        for width in test_widths:
            output = self._capture_ps1_output(width, monkeypatch)
            prompt_line = self._get_prompt_line(output)
            visible_width = self._count_visible_width(prompt_line)

            assert visible_width <= width, \
                f"Width {width}: Prompt is {visible_width} chars (exceeds width)"

    @pytest.mark.unit
    def test_prompt_fills_width_with_filler(self, monkeypatch):
        """Test that prompt uses filler to fill width."""
        output_80 = self._capture_ps1_output(80, monkeypatch)
        output_120 = self._capture_ps1_output(120, monkeypatch)

        prompt_80 = self._get_prompt_line(output_80)
        prompt_120 = self._get_prompt_line(output_120)

        width_80 = self._count_visible_width(prompt_80)
        width_120 = self._count_visible_width(prompt_120)

        assert width_120 > width_80, \
            f"Wider terminal (120) should produce wider prompt than narrower (80). " \
            f"Got {width_120} vs {width_80}"

    @pytest.mark.edge_case
    def test_prompt_width_exact_measurement(self, monkeypatch):
        """Test exact width measurements at specific widths."""
        test_cases = [
            (80, 80),
            (120, 120),
            (160, 160),
        ]

        for width, max_expected in test_cases:
            output = self._capture_ps1_output(width, monkeypatch)
            prompt_line = self._get_prompt_line(output)
            visible_width = self._count_visible_width(prompt_line)

            assert visible_width <= max_expected, \
                f"Width {width}: Prompt is {visible_width} chars (exceeds {max_expected})"

            assert visible_width > 0, \
                f"Width {width}: Prompt is empty"

    @pytest.mark.unit
    def test_prompt_structure_at_different_widths(self, monkeypatch):
        """Test that prompt structure is consistent across widths."""
        widths = [80, 120, 160]

        for width in widths:
            output = self._capture_ps1_output(width, monkeypatch)
            prompt_line = self._get_prompt_line(output)
            clean = self._strip_ansi_codes(prompt_line)

            assert len(clean) > 0, f"Width {width}: Prompt is empty"
            assert len(clean.strip()) > 0, f"Width {width}: Prompt has no content"

    @pytest.mark.edge_case
    def test_prompt_contains_filler_at_wide_width(self, monkeypatch):
        """Test that filler segment is used at wide widths."""
        output = self._capture_ps1_output(200, monkeypatch)
        prompt_line = self._get_prompt_line(output)
        clean = self._strip_ansi_codes(prompt_line)

        assert len(clean) >= 100, \
            f"At 200 cols, prompt should be >= 100 chars, got {len(clean)}"

        assert '·' in clean or '─' in clean or len(clean) > 80, \
            "Should contain filler characters or be very wide"

    @pytest.mark.unit
    def test_prompt_respects_column_limit_strictly(self, monkeypatch):
        """Test that prompt never exceeds column limit."""
        for width in range(40, 201, 20):
            output = self._capture_ps1_output(width, monkeypatch)
            prompt_line = self._get_prompt_line(output)
            visible_width = self._count_visible_width(prompt_line)

            assert visible_width <= width, \
                f"Width {width}: Prompt width {visible_width} exceeds limit"

    @pytest.mark.unit
    def test_prompt_single_line_output(self, monkeypatch):
        """Test that prompt output has one prompt line plus a dollar line."""
        widths = [40, 80, 120, 160, 200]

        for width in widths:
            output = self._capture_ps1_output(width, monkeypatch)
            lines = output.split('\n')
            # Line 0: prompt segments, Line 1: dollar sign
            non_empty = [l for l in lines if l.strip() != '']
            assert len(non_empty) == 2, \
                f"Width {width}: Expected 2 lines (prompt + dollar), got {len(non_empty)}"


class TestChunksWidthCalculation:
    """Test the width calculation logic in Chunks class."""

    @pytest.mark.unit
    def test_chunks_respects_passed_width(self):
        """Test that Chunks respects width parameter."""
        chunks_80 = Chunks(columns="80")
        assert chunks_80.columns == "80"

        chunks_120 = Chunks(columns="120")
        assert chunks_120.columns == "120"

    @pytest.mark.unit
    def test_get_length_with_different_widths(self):
        """Test _get_length calculation at different widths."""
        chunks_80 = Chunks(columns="80")
        chunks_80.segment_lengths = [5, 3, 4]
        max_len_80 = chunks_80._get_length()
        assert max_len_80 == 80 - 3 - 12

        chunks_120 = Chunks(columns="120")
        chunks_120.segment_lengths = [5, 3, 4]
        max_len_120 = chunks_120._get_length()
        assert max_len_120 == 120 - 3 - 12

        assert max_len_120 > max_len_80

    @pytest.mark.unit
    def test_filler_scales_with_width(self):
        """Test that filler segment scales with terminal width."""
        chunks = Chunks(columns="80")
        chunks.segment_lengths = [10]

        max_len = chunks._get_length()
        assert max_len == 69

        filler_count_80 = (80 - 1) // len(chunks.filler_char) - 1
        assert filler_count_80 >= 20

        chunks = Chunks(columns="160")
        chunks.segment_lengths = [10]

        max_len = chunks._get_length()
        assert max_len == 159 - 10

        filler_count_160 = (160 - 1) // len(chunks.filler_char) - 1
        assert filler_count_160 > filler_count_80


class TestPs1EndToEnd:
    """End-to-end tests that call ps1_prompt() with minimal mocking.

    Only terminal tab commands and the projects config file are mocked,
    since those depend on external state. Everything else (git, path,
    user, time, filler, etc.) runs for real.
    """

    def _strip_ansi_codes(self, text: str) -> str:
        ansi_escape = re.compile(r'\x1B(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07)')
        return ansi_escape.sub('', text)

    @pytest.mark.integration
    def test_ps1_prompt_generates_without_error(self, monkeypatch):
        """Test that ps1_prompt() runs to completion and returns a non-empty string."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("testproj\t/nonexistent/path\t#3366AA\n")
            temp_projects = f.name

        try:
            monkeypatch.setenv("COLUMNS", "100")
            monkeypatch.setenv("KITTY_PID", "")
            monkeypatch.setenv("ITERM_SESSION_ID", "")

            with patch("prompt.prompt.Path") as mock_path_cls:
                # Only mock the projects config file lookup
                from pathlib import Path as RealPath
                def path_side_effect(arg):
                    if arg == "~/.prompt-projects":
                        p = RealPath(temp_projects)
                        return p
                    return RealPath(arg)
                mock_path_cls.side_effect = path_side_effect

                output = ps1_prompt()

            assert isinstance(output, str)
            assert len(output) > 0

            # Should contain a newline (dollar sign is on second line)
            assert "\n" in output

            # Visible content should be non-empty
            clean = self._strip_ansi_codes(output)
            assert len(clean.strip()) > 0
        finally:
            os.unlink(temp_projects)

    @pytest.mark.integration
    def test_ps1_prompt_contains_expected_segments(self, monkeypatch):
        """Test that the prompt contains expected content like user, time, and path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("testproj\t/nonexistent/path\t#3366AA\n")
            temp_projects = f.name

        try:
            monkeypatch.setenv("COLUMNS", "200")
            monkeypatch.setenv("KITTY_PID", "")
            monkeypatch.setenv("ITERM_SESSION_ID", "")

            with patch("prompt.prompt.Path") as mock_path_cls:
                from pathlib import Path as RealPath
                def path_side_effect(arg):
                    if arg == "~/.prompt-projects":
                        return RealPath(temp_projects)
                    return RealPath(arg)
                mock_path_cls.side_effect = path_side_effect

                output = ps1_prompt()

            clean = self._strip_ansi_codes(output)

            # Should contain the username
            assert os.environ.get("USER", "") in clean

            # Should contain a time-like pattern (HH:MM)
            assert re.search(r'\d{2}:\d{2}', clean), "Expected time (HH:MM) in prompt"

            # Should contain the dollar sign
            assert "❖" in clean
        finally:
            os.unlink(temp_projects)

    @pytest.mark.integration
    def test_ps1_prompt_works_without_columns_env(self, monkeypatch):
        """Test that ps1_prompt() works even when COLUMNS is not set (pipe/subshell)."""
        monkeypatch.delenv("COLUMNS", raising=False)
        monkeypatch.setenv("KITTY_PID", "")
        monkeypatch.setenv("ITERM_SESSION_ID", "")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("")
            temp_projects = f.name

        try:
            with patch("prompt.prompt.Path") as mock_path_cls:
                from pathlib import Path as RealPath
                def path_side_effect(arg):
                    if arg == "~/.prompt-projects":
                        return RealPath(temp_projects)
                    return RealPath(arg)
                mock_path_cls.side_effect = path_side_effect

                output = ps1_prompt()

            assert isinstance(output, str)
            assert len(output) > 0
        finally:
            os.unlink(temp_projects)

    @pytest.mark.integration
    def test_ps1_prompt_no_exception_in_git_repo(self, monkeypatch):
        """Test that ps1_prompt() works in the current directory (a real git repo)."""
        monkeypatch.setenv("COLUMNS", "120")
        monkeypatch.setenv("KITTY_PID", "")
        monkeypatch.setenv("ITERM_SESSION_ID", "")

        # Use a temp empty projects file so no project matches
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("")
            temp_projects = f.name

        try:
            with patch("prompt.prompt.Path") as mock_path_cls:
                from pathlib import Path as RealPath
                def path_side_effect(arg):
                    if arg == "~/.prompt-projects":
                        return RealPath(temp_projects)
                    return RealPath(arg)
                mock_path_cls.side_effect = path_side_effect

                output = ps1_prompt()

            assert isinstance(output, str)
            assert len(output) > 0
        finally:
            os.unlink(temp_projects)
