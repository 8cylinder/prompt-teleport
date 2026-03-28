"""Tests for CLI commands in ui.py module."""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from prompt.ui import prompt


class TestPromptCommand:
    """Test main prompt command."""

    @pytest.mark.integration
    def test_prompt_help(self):
        """Test that main prompt command shows help."""
        runner = CliRunner()
        result = runner.invoke(prompt, ["--help"])
        assert result.exit_code == 0
        assert "Output a PS1 prompt" in result.output

    @pytest.mark.integration
    def test_prompt_version(self):
        """Test prompt version output."""
        runner = CliRunner()
        result = runner.invoke(prompt, ["--version"])
        assert result.exit_code == 0
        # Should output version number
        assert "0." in result.output


class TestPs1Command:
    """Test ps1 subcommand."""

    @pytest.mark.integration
    def test_ps1_command_runs(self):
        """Test that ps1 command executes."""
        runner = CliRunner()
        with patch("os.environ.get") as mock_get:
            mock_get.side_effect = lambda key, default="": {
                "SSH_CLIENT": "",
                "HOME": "/home/user",
                "USER": "testuser",
            }.get(key, default)

            with patch("os.get_terminal_size", return_value=os.terminal_size((80, 24))):

                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = ""

                    result = runner.invoke(prompt, ["ps1"])
                    assert result.exit_code == 0

    @pytest.mark.integration
    def test_ps1_help(self):
        """Test ps1 help output."""
        runner = CliRunner()
        result = runner.invoke(prompt, ["ps1", "--help"])
        assert result.exit_code == 0
        assert "Output a PS1 prompt" in result.output


class TestThemesCommand:
    """Test themes subcommand."""

    @pytest.mark.integration
    def test_themes_command_runs(self):
        """Test that themes command executes."""
        runner = CliRunner()
        result = runner.invoke(prompt, ["themes"])
        assert result.exit_code == 0
        # Should output theme names
        assert "Local" in result.output or "Remote" in result.output

    @pytest.mark.integration
    def test_themes_help(self):
        """Test themes help output."""
        runner = CliRunner()
        result = runner.invoke(prompt, ["themes", "--help"])
        assert result.exit_code == 0
        assert "Show the themes" in result.output


class TestProjectCommand:
    """Test project subcommand group."""

    @pytest.mark.integration
    def test_project_help(self):
        """Test project subcommand help."""
        runner = CliRunner()
        result = runner.invoke(prompt, ["project", "--help"])
        assert result.exit_code == 0
        assert "teleport to a project" in result.output or "cd" in result.output


class TestProjectCdCommand:
    """Test project cd subcommand."""

    @pytest.mark.integration
    def test_project_cd_help(self):
        """Test project cd help output."""
        runner = CliRunner()
        result = runner.invoke(prompt, ["project", "cd", "--help"])
        assert result.exit_code == 0
        assert "Teleport to a project" in result.output

    @pytest.mark.integration
    def test_project_cd_no_args(self):
        """Test project cd with no arguments requires PROJECT_NAME."""
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("project1\t/home/user/project1\t#FF0000\n")
            temp_file = f.name

        try:
            with patch("prompt.projects.CONFIG_FILE", temp_file):
                result = runner.invoke(prompt, ["project", "cd"])
                # PROJECT_NAME is required, so should fail with usage error
                assert result.exit_code != 0
                assert "Missing argument" in result.output or "PROJECT_NAME" in result.output
        finally:
            os.unlink(temp_file)

    @pytest.mark.integration
    def test_project_cd_with_matching_project(self):
        """Test project cd with matching project name."""
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("myproject\t/home/user/myproject\t#FF0000\n")
            temp_file = f.name

        try:
            with patch("prompt.projects.CONFIG_FILE", temp_file):
                result = runner.invoke(prompt, ["project", "cd", "myproject"])
                assert "cd /home/user/myproject" in result.output
        finally:
            os.unlink(temp_file)

    @pytest.mark.integration
    def test_project_cd_with_partial_match(self):
        """Test project cd with partial project name."""
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("myproject\t/home/user/myproject\t#FF0000\n")
            f.write("myproject2\t/home/user/myproject2\t#00FF00\n")
            temp_file = f.name

        try:
            with patch("prompt.projects.CONFIG_FILE", temp_file):
                result = runner.invoke(prompt, ["project", "cd", "my"])
                # Should show both projects
                assert "myproject" in result.output
                assert "myproject2" in result.output
        finally:
            os.unlink(temp_file)

    @pytest.mark.edge_case
    def test_project_cd_no_matches(self):
        """Test project cd with no matching projects."""
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("project1\t/home/user/project1\t#FF0000\n")
            temp_file = f.name

        try:
            with patch("prompt.projects.CONFIG_FILE", temp_file):
                result = runner.invoke(prompt, ["project", "cd", "nomatch"])
                # Should show error
                assert "nomatch" in result.output or "Error" in result.output or result.exit_code != 0
        finally:
            os.unlink(temp_file)


class TestProjectAddCommand:
    """Test project add subcommand."""

    @pytest.mark.integration
    def test_project_add_help(self):
        """Test project add help output."""
        runner = CliRunner()
        result = runner.invoke(prompt, ["project", "add", "--help"])
        assert result.exit_code == 0
        assert "Add a project" in result.output

    @pytest.mark.integration
    def test_project_add_with_color(self):
        """Test adding a project with specified color."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "myproject"
            project_dir.mkdir()

            with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
                temp_file = f.name

            try:
                with patch("prompt.projects.CONFIG_FILE", temp_file):
                    result = runner.invoke(
                        prompt,
                        ["project", "add", "newproject", str(project_dir), "-c", "#FF0000"]
                    )
                    assert result.exit_code == 0

                    # Verify project was added
                    with open(temp_file, "r") as f:
                        content = f.read()
                        assert "newproject" in content
                        assert "#FF0000" in content
            finally:
                os.unlink(temp_file)

    @pytest.mark.integration
    def test_project_add_without_color(self):
        """Test adding a project with auto-generated color."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "myproject"
            project_dir.mkdir()

            with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
                temp_file = f.name

            try:
                with patch("prompt.projects.CONFIG_FILE", temp_file):
                    result = runner.invoke(
                        prompt,
                        ["project", "add", "newproject", str(project_dir)]
                    )
                    assert result.exit_code == 0

                    # Verify project was added with some color
                    with open(temp_file, "r") as f:
                        content = f.read()
                        assert "newproject" in content
                        assert "#" in content  # Should have hex color
            finally:
                os.unlink(temp_file)

    @pytest.mark.edge_case
    def test_project_add_invalid_color(self):
        """Test adding project with invalid color fails."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "myproject"
            project_dir.mkdir()

            with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
                temp_file = f.name

            try:
                with patch("prompt.projects.CONFIG_FILE", temp_file):
                    result = runner.invoke(
                        prompt,
                        ["project", "add", "newproject", str(project_dir), "-c", "notacolor"]
                    )
                    # Should fail with invalid color
                    assert result.exit_code != 0
            finally:
                os.unlink(temp_file)

    @pytest.mark.edge_case
    def test_project_add_nonexistent_directory(self):
        """Test adding project with nonexistent directory fails."""
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            temp_file = f.name

        try:
            with patch("prompt.projects.CONFIG_FILE", temp_file):
                result = runner.invoke(
                    prompt,
                    ["project", "add", "newproject", "/nonexistent/path", "-c", "red"]
                )
                # Should fail because directory doesn't exist
                assert result.exit_code != 0
        finally:
            os.unlink(temp_file)
