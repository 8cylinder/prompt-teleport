"""Shared fixtures and configuration for tests."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_projects_file():
    """Create a temporary projects configuration file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        f.write("# Test projects file\n")
        f.write("project1\t/home/user/projects/project1\t#FF0000\n")
        f.write("project2\t/home/user/projects/project2\t#00FF00\n")
        f.write("nested\t/home/user/projects/nested/deep\t#0000FF\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_environment(monkeypatch):
    """Provide a fixture to mock environment variables."""
    def set_env(**kwargs):
        for key, value in kwargs.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)
    return set_env
