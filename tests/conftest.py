"""Shared test fixtures for pydsettingsforge."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with a basic pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "myapp"\n'
        'version = "1.0.0"\n'
        'description = "A test app"\n'
        "\n"
        "[tool.myapp]\n"
        "debug = false\n"
        'log_level = "info"\n'
        "\n"
        "[tool.myapp.database]\n"
        'host = "localhost"\n'
        "port = 5432\n"
    )
    return tmp_path


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    """Create a temporary .env file."""
    env = tmp_path / ".env"
    env.write_text("DEBUG=true\nLOG_LEVEL=debug\n")
    return env


@pytest.fixture
def nested_env_file(tmp_path: Path) -> Path:
    """Create a temporary .env file with nested keys."""
    env = tmp_path / ".env.nested"
    env.write_text("DATABASE__HOST=db.example.com\nDATABASE__PORT=3306\n")
    return env
