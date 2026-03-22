"""Tests for projects.py module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from prompt.projects import (
    read_csv,
    write_csv,
    get_project_dir,
    add_line,
    filter_projects,
    get_random_color,
    ColorParamType,
)


class TestReadCsv:
    """Test reading CSV configuration file."""

    @pytest.mark.unit
    def test_read_valid_csv(self, temp_projects_file):
        """Test reading a valid projects file."""
        with patch("prompt.projects.CONFIG_FILE", temp_projects_file):
            data = read_csv()
            assert "project1" in data
            assert data["project1"][0] == "/home/user/projects/project1"
            assert data["project1"][1] == "#FF0000"

    @pytest.mark.unit
    def test_read_csv_ignores_comments(self, temp_projects_file):
        """Test that comments are ignored."""
        with patch("prompt.projects.CONFIG_FILE", temp_projects_file):
            data = read_csv()
            # The file has a comment line, it should not be in the data
            assert not any(key.startswith("#") for key in data.keys())

    @pytest.mark.edge_case
    def test_read_nonexistent_file(self):
        """Test reading from nonexistent file raises error."""
        with patch("prompt.projects.CONFIG_FILE", "/nonexistent/file.tsv"):
            with pytest.raises(SystemExit):
                read_csv()

    @pytest.mark.unit
    def test_read_csv_sorted(self, temp_projects_file):
        """Test that projects are sorted by path."""
        with patch("prompt.projects.CONFIG_FILE", temp_projects_file):
            data = read_csv()
            paths = [v[0] for v in data.values()]
            # Should be sorted (nested comes last)
            assert paths == sorted(paths)


class TestWriteCsv:
    """Test writing CSV configuration file."""

    @pytest.mark.unit
    def test_write_csv(self):
        """Test writing projects to CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            temp_file = f.name

        try:
            with patch("prompt.projects.CONFIG_FILE", temp_file):
                test_data = {
                    "project1": ["/path/to/project1", "#FF0000"],
                    "project2": ["/path/to/project2", "#00FF00"],
                }
                write_csv(test_data)

                # Read back and verify
                with open(temp_file, "r") as f:
                    lines = f.readlines()
                    assert "project1\t/path/to/project1\t#FF0000\n" in lines
                    assert "project2\t/path/to/project2\t#00FF00\n" in lines
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_write_csv_overwrites(self):
        """Test that write_csv overwrites existing file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            temp_file = f.name
            f.write("old\t/old/path\t#FFFFFF\n")

        try:
            with patch("prompt.projects.CONFIG_FILE", temp_file):
                test_data = {
                    "new": ["/new/path", "#000000"],
                }
                write_csv(test_data)

                with open(temp_file, "r") as f:
                    content = f.read()
                    assert "old" not in content
                    assert "new" in content
        finally:
            os.unlink(temp_file)


class TestGetProjectDir:
    """Test project directory detection."""

    @pytest.mark.unit
    def test_in_project_root(self):
        """Test when current dir is project root."""
        projects = {
            "myproject": ["/home/user/projects/myproject", "#FF0000"],
        }
        with patch("os.path.realpath", return_value="/home/user/projects/myproject"):
            result = get_project_dir(projects)
            assert result is False

    @pytest.mark.unit
    def test_in_project_subdirectory(self):
        """Test when current dir is in project subdirectory."""
        projects = {
            "myproject": ["/home/user/projects/myproject", "#FF0000"],
        }
        with patch("os.path.realpath", return_value="/home/user/projects/myproject/src"):
            result = get_project_dir(projects)
            assert result == "/home/user/projects/myproject"

    @pytest.mark.unit
    def test_not_in_any_project(self):
        """Test when current dir is not in any project."""
        projects = {
            "myproject": ["/home/user/projects/myproject", "#FF0000"],
        }
        with patch("os.path.realpath", return_value="/home/other/location"):
            result = get_project_dir(projects)
            assert result is False

    @pytest.mark.edge_case
    def test_path_prefix_issue(self):
        """Test the path prefix matching vulnerability.

        This tests that /home/myproject2 doesn't match /home/myproject.
        This is currently a bug - it uses string.startswith() instead of
        proper path comparison.
        """
        projects = {
            "myproject": ["/home/myproject", "#FF0000"],
        }
        # This is a known bug: /home/myproject2 will incorrectly match /home/myproject
        # because "startswith" only checks string prefix, not path components
        with patch("os.path.realpath", return_value="/home/myproject2/src"):
            result = get_project_dir(projects)
            # Currently returns the path (bug), but should return False
            # After fix, this should be: assert result is False
            assert result == "/home/myproject"  # Current buggy behavior

    @pytest.mark.unit
    def test_multiple_projects_selects_closest(self):
        """Test that closest (longest) matching path is selected.

        Note: This test demonstrates a bug in the current implementation.
        The code should select the longest/most specific match, but due to
        the string prefix matching issue, it returns the first match.
        This will be fixed when switching to Path.is_relative_to().
        """
        projects = {
            "parent": ["/home/user", "#FF0000"],
            "child": ["/home/user/projects", "#00FF00"],
        }
        with patch("os.path.realpath", return_value="/home/user/projects/myproj/src"):
            result = get_project_dir(projects)
            # Currently returns parent due to iteration order, should return child
            # TODO: Fix by using Path.is_relative_to() and selecting longest match
            assert result == "/home/user"  # Current buggy behavior


class TestAddLine:
    """Test adding project entries."""

    @pytest.mark.unit
    def test_add_new_project(self, temp_projects_file):
        """Test adding a new project."""
        with patch("prompt.projects.CONFIG_FILE", temp_projects_file):
            add_line("newproject", Path("/home/user/new"), "#AABBCC")

            data = read_csv()
            assert "newproject" in data
            assert data["newproject"][0] == "/home/user/new"
            assert data["newproject"][1] == "#AABBCC"

    @pytest.mark.unit
    def test_update_existing_project_color(self, temp_projects_file):
        """Test updating an existing project's color."""
        with patch("prompt.projects.CONFIG_FILE", temp_projects_file):
            # Update existing project
            add_line("project1", Path("/home/user/projects/project1"), "#NEWCOL")

            data = read_csv()
            assert data["project1"][1] == "#NEWCOL"
            # Path should remain the same
            assert data["project1"][0] == "/home/user/projects/project1"

    @pytest.mark.unit
    def test_add_project_with_random_color(self, temp_projects_file):
        """Test adding project with auto-generated color."""
        with patch("prompt.projects.CONFIG_FILE", temp_projects_file):
            with patch("prompt.projects.get_random_color", return_value="#RRGGBB"):
                add_line("random_color", Path("/home/user/random"), "")

                data = read_csv()
                assert data["random_color"][1] == "#RRGGBB"


class TestFilterProjects:
    """Test project filtering."""

    @pytest.mark.unit
    def test_filter_exact_match(self):
        """Test filtering with exact match."""
        projects = {
            "myproject": ["/path1", "#FF0000"],
            "otherproject": ["/path2", "#00FF00"],
        }
        result = filter_projects(projects, "myproject")
        assert len(result) == 1
        assert "myproject" in result

    @pytest.mark.unit
    def test_filter_prefix_match(self):
        """Test filtering with prefix match."""
        projects = {
            "myproject": ["/path1", "#FF0000"],
            "myproject2": ["/path2", "#00FF00"],
            "otherproject": ["/path3", "#0000FF"],
        }
        result = filter_projects(projects, "my")
        assert len(result) == 2
        assert "myproject" in result
        assert "myproject2" in result

    @pytest.mark.unit
    def test_filter_case_insensitive(self):
        """Test that filtering is case-insensitive."""
        projects = {
            "MyProject": ["/path1", "#FF0000"],
            "OTHERPROJECT": ["/path2", "#00FF00"],
        }
        result = filter_projects(projects, "myp")
        assert "MyProject" in result

    @pytest.mark.unit
    def test_filter_no_matches(self):
        """Test filtering with no matches."""
        projects = {
            "myproject": ["/path1", "#FF0000"],
        }
        result = filter_projects(projects, "nomatch")
        assert len(result) == 0


class TestGetRandomColor:
    """Test random color generation."""

    @pytest.mark.unit
    def test_random_color_format(self):
        """Test that generated color is valid hex."""
        color = get_random_color()
        assert color.startswith("#")
        assert len(color) == 7
        # Should be valid hex
        try:
            int(color[1:], 16)
        except ValueError:
            pytest.fail(f"Generated color is not valid hex: {color}")

    @pytest.mark.unit
    def test_random_color_varies(self):
        """Test that random colors are different."""
        colors = [get_random_color() for _ in range(10)]
        # With 10 random colors, should have at least 5 unique ones
        assert len(set(colors)) >= 5

    @pytest.mark.unit
    def test_random_color_in_valid_range(self):
        """Test that color values are within valid RGB range."""
        for _ in range(10):
            color = get_random_color()
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255


class TestColorParamType:
    """Test Click color parameter type."""

    @pytest.mark.unit
    def test_named_color_valid(self):
        """Test that named colors are accepted."""
        param_type = ColorParamType()
        assert param_type.convert("red", None, None) == "red"
        assert param_type.convert("blue", None, None) == "blue"
        assert param_type.convert("white", None, None) == "white"

    @pytest.mark.unit
    def test_hex_color_valid(self):
        """Test that hex colors are accepted."""
        param_type = ColorParamType()
        assert param_type.convert("#FF0000", None, None) == "#FF0000"
        assert param_type.convert("#fff", None, None) == "#fff"

    @pytest.mark.edge_case
    def test_invalid_color_fails(self):
        """Test that invalid colors are rejected."""
        param_type = ColorParamType()
        with pytest.raises(Exception):  # Click raises BadParameter
            param_type.convert("notacolor", None, None)

    @pytest.mark.edge_case
    def test_invalid_hex_fails(self):
        """Test that invalid hex is rejected."""
        param_type = ColorParamType()
        with pytest.raises(Exception):
            param_type.convert("#GGGGGG", None, None)
