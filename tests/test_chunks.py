"""Tests for Chunks class and prompt generation."""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from prompt.prompt import Chunks, Segment


class TestChunksInit:
    """Test Chunks class initialization."""

    @pytest.mark.unit
    def test_chunks_init_local(self):
        """Test Chunks initialization in local environment."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                assert chunks.theme is not None
                assert "PATH" in str(chunks.theme)  # Theme should have PATH segment

    @pytest.mark.unit
    def test_chunks_init_ssh(self):
        """Test Chunks initialization in SSH environment."""
        with patch.dict(os.environ, {"SSH_CLIENT": "192.168.1.1"}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                # Should use Remote theme
                assert chunks.theme is not None

    @pytest.mark.edge_case
    def test_chunks_init_no_terminal_falls_back_to_stty(self):
        """Test Chunks falls back to stty when os.get_terminal_size fails."""
        with patch("os.get_terminal_size", side_effect=OSError("not a terminal")):
            with patch("os.popen") as mock_popen:
                mock_popen.return_value.read.return_value = "24 120"
                chunks = Chunks()
                assert chunks.columns == "120"

    @pytest.mark.edge_case
    def test_chunks_init_no_terminal_falls_back_to_default(self):
        """Test Chunks falls back to 80 when both detection methods fail."""
        with patch("os.get_terminal_size", side_effect=OSError("not a terminal")):
            with patch("os.popen") as mock_popen:
                mock_popen.return_value.read.return_value = ""
                chunks = Chunks()
                assert chunks.columns == "80"

    @pytest.mark.unit
    def test_chunks_segment_lengths_tracking(self):
        """Test that segment lengths are tracked."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                assert chunks.segment_lengths == []
                chunks._add_length("test")
                assert chunks.segment_lengths == [4]


class TestChunkApplyTheme:
    """Test apply_chunk_theme method."""

    @pytest.mark.unit
    def test_apply_theme_path_segment(self):
        """Test applying theme to PATH segment."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                result = chunks.apply_chunk_theme(Segment.PATH, ("/home/user",))
                assert result  # Should return some string
                assert isinstance(result, str)

    @pytest.mark.unit
    def test_apply_theme_user_segment(self):
        """Test applying theme to USER segment."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                result = chunks.apply_chunk_theme(Segment.USER, ("user@hostname",))
                assert result
                assert isinstance(result, str)

    @pytest.mark.unit
    def test_apply_theme_dollar_segment_no_styling(self):
        """Test that DOLLAR segment returns unstyled."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                result = chunks.apply_chunk_theme(Segment.DOLLAR, ("$ ",))
                # DOLLAR segment should return unstyled text
                assert "$ " in result

    @pytest.mark.unit
    def test_apply_theme_multiple_chunks(self):
        """Test applying theme with multiple chunks (split path)."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                result = chunks.apply_chunk_theme(
                    Segment.PATH,
                    ("/home", "user"),
                    split_char="…"
                )
                assert result
                assert isinstance(result, str)

    @pytest.mark.edge_case
    def test_apply_theme_sink_no_project(self):
        """Test SINK segment when no project is found."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                # Mock get_project_info to return empty project
                with patch.object(chunks, "get_project_info", return_value=("", "blue", "white")):
                    result = chunks.apply_chunk_theme(Segment.SINK, ("",))
                    # Should return empty string when no project
                    assert result == ""


class TestChunkGetLength:
    """Test _get_length calculation."""

    @pytest.mark.unit
    def test_get_length_calculation(self):
        """Test terminal width calculation."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                chunks.segment_lengths = [5, 3, 4]  # Total: 12
                # max_len = 80 - (3 segments) - 12 (sum of lengths)
                max_len = chunks._get_length()
                assert max_len == 80 - 3 - 12

    @pytest.mark.unit
    def test_get_length_with_extra(self):
        """Test length calculation with extra string."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                chunks.segment_lengths = [5]
                max_len = chunks._get_length(extra="test")
                # Should account for extra string length
                assert max_len == 80 - 1 - 5 - 4


class TestGetChunk:
    """Test get_chunk dispatcher method."""

    @pytest.mark.unit
    def test_get_chunk_path(self):
        """Test getting PATH chunk."""
        with patch.dict(os.environ, {"SSH_CLIENT": "", "HOME": "/home/user"}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                # Mock the path method
                with patch.object(chunks, "_chunk_path", return_value="/home/user"):
                    result = chunks.get_chunk(Segment.PATH)
                    assert result == "/home/user"

    @pytest.mark.unit
    def test_get_chunk_time(self):
        """Test getting TIME chunk."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                result = chunks.get_chunk(Segment.TIME)
                assert result  # Should return a time string
                # Should be in HH:MM format
                assert ":" in result

    @pytest.mark.unit
    def test_get_chunk_user(self):
        """Test getting USER chunk."""
        with patch.dict(os.environ, {"SSH_CLIENT": "", "USER": "testuser"}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                with patch.object(Chunks, "HOSTNAME", "testhost"):
                    result = chunks.get_chunk(Segment.USER)
                    assert "testuser" in result
                    assert "testhost" in result

    @pytest.mark.edge_case
    def test_get_chunk_invalid_segment(self):
        """Test getting invalid segment raises error."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                # Create a mock invalid segment
                invalid_segment = MagicMock()
                invalid_segment.name = "invalid"

                with pytest.raises(SystemExit):
                    chunks.get_chunk(invalid_segment)


class TestGetProjectInfo:
    """Test project information retrieval."""

    @pytest.mark.unit
    def test_get_project_info_found(self, temp_projects_file):
        """Test getting project info when project is found."""
        # Create a temp projects file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("myproject\t/home/user/myproject\t#FF0000\n")
            temp_file = f.name

        try:
            with patch.dict(os.environ, {"SSH_CLIENT": "", "KITTY_PID": "", "ITERM_SESSION_ID": ""}):
                with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                    chunks = Chunks()
                    with patch("prompt.prompt.Path") as mock_path:
                        mock_path.return_value.expanduser.return_value = temp_file
                        with patch("os.path.curdir", "/home/user/myproject/src"):
                            with patch("os.path.abspath") as mock_abs:
                                mock_abs.return_value = "/home/user/myproject/src"
                                with patch.object(Path, "is_relative_to", return_value=True):
                                    name, bg, fg = chunks.get_project_info()
                                    assert name == "myproject"
                                    assert bg == "#FF0000"
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_get_project_info_not_found(self):
        """Test getting project info when not in a project."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("someproject\t/some/path\t#FF0000\n")
            temp_file = f.name

        try:
            with patch.dict(os.environ, {"SSH_CLIENT": "", "KITTY_PID": "", "ITERM_SESSION_ID": ""}):
                with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                    chunks = Chunks()
                    # Mock the config file location
                    with patch("pathlib.Path.expanduser") as mock_expand:
                        mock_expand.return_value = Path(temp_file)
                        # Mock the current directory to be somewhere not in any project
                        with patch("os.path.curdir", "/other/location"):
                            with patch("os.path.abspath") as mock_abs:
                                mock_abs.return_value = "/other/location"
                                name, bg, fg = chunks.get_project_info()
                                # Should return defaults when not in any project
                                assert name == ""
                                assert bg == "blue"  # Default
                                assert fg == "white"  # Default
        finally:
            os.unlink(temp_file)

    @pytest.mark.edge_case
    def test_get_project_info_missing_file(self):
        """Test get_project_info with missing config file."""
        with patch.dict(os.environ, {"SSH_CLIENT": "", "KITTY_PID": "", "ITERM_SESSION_ID": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()
                with patch("prompt.prompt.Path") as mock_path:
                    mock_path.return_value.expanduser.return_value = "/nonexistent/file"
                    with patch("builtins.open", side_effect=FileNotFoundError):
                        # Should not crash, should return defaults
                        name, bg, fg = chunks.get_project_info()
                        assert name == ""
                        assert bg == "blue"


class TestChunkSpecificMethods:
    """Test individual _chunk_* methods."""

    @pytest.mark.unit
    def test_chunk_venv_when_set(self):
        """Test VENV chunk when VIRTUAL_ENV is set."""
        with patch.dict(os.environ, {
            "SSH_CLIENT": "",
            "VIRTUAL_ENV": "/home/user/.venv/myenv",
            "POETRY_ACTIVE": ""
        }):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                result = chunks._chunk_venv()
                assert "myenv" in result

    @pytest.mark.unit
    def test_chunk_venv_when_not_set(self):
        """Test VENV chunk when VIRTUAL_ENV is not set."""
        with patch.dict(os.environ, {
            "SSH_CLIENT": "",
            "VIRTUAL_ENV": "",
        }, clear=False):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                result = chunks._chunk_venv()
                assert result == ""

    @pytest.mark.unit
    def test_chunk_ssh_when_connected(self):
        """Test SSH chunk when connected via SSH."""
        with patch.dict(os.environ, {"SSH_CLIENT": "192.168.1.1"}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                result = chunks._chunk_ssh()
                assert "ssh" in result

    @pytest.mark.unit
    def test_chunk_ssh_when_local(self):
        """Test SSH chunk when not connected."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()

                result = chunks._chunk_ssh()
                assert result == ""


class TestGitSkipOptimization:
    """Test that git subprocess is skipped in non-git directories."""

    @pytest.mark.unit
    def test_branch_skips_git_when_not_in_repo(self):
        """Test that _chunk_branch returns empty without calling subprocess in non-git dirs."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()
                chunks._dir_markers[".git"] = None

                with patch("subprocess.run") as mock_run:
                    result = chunks._chunk_branch()
                    assert result == ""
                    mock_run.assert_not_called()

    @pytest.mark.unit
    def test_branch_calls_git_when_in_repo(self):
        """Test that _chunk_branch does call git when .git marker is present."""
        with patch.dict(os.environ, {"SSH_CLIENT": ""}):
            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):
                chunks = Chunks()
                chunks._dir_markers[".git"] = Path("/some/repo/.git")

                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.stdout = "## main...origin/main\n"
                    result = chunks._chunk_branch()
                    mock_run.assert_called_once()
