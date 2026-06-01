"""Tests for toml_reader module."""

from pathlib import Path

import pytest

from settingsforge.exceptions import (
    PyprojectNotFoundError,
    RootSectionNotFoundError,
    ToolSectionNotFoundError,
)
from settingsforge.toml_reader import (
    extract_settings,
    read_pyproject,
    resolve_pyproject_path,
)


class TestResolvePyprojectPath:
    def test_with_explicit_path(self, tmp_path: Path) -> None:
        custom = tmp_path / "custom.toml"
        result = resolve_pyproject_path(custom)
        assert result == custom

    def test_defaults_to_cwd(self) -> None:
        result = resolve_pyproject_path(None)
        assert result.name == "pyproject.toml"
        assert result.parent == Path.cwd()


class TestReadPyproject:
    def test_reads_valid_file(self, tmp_project: Path) -> None:
        path = tmp_project / "pyproject.toml"
        data = read_pyproject(path)
        assert data["project"]["name"] == "myapp"
        assert data["project"]["version"] == "1.0.0"

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(PyprojectNotFoundError):
            read_pyproject(tmp_path / "nonexistent.toml")


class TestExtractSettings:
    def test_top_level_only(self) -> None:
        data = {
            "project": {"name": "myapp", "version": "1.0.0"},
        }
        result = extract_settings(data)
        assert result == {"name": "myapp", "version": "1.0.0"}

    def test_with_tool_section(self) -> None:
        data = {
            "project": {"name": "myapp"},
            "tool": {"myapp": {"debug": False, "log_level": "info"}},
        }
        result = extract_settings(data, tool_section="myapp")
        assert result == {"name": "myapp", "debug": False, "log_level": "info"}

    def test_tool_section_not_found(self) -> None:
        data = {"project": {"name": "myapp"}, "tool": {}}
        with pytest.raises(ToolSectionNotFoundError):
            extract_settings(data, tool_section="missing")

    def test_nested_tool_section(self) -> None:
        data = {
            "project": {},
            "tool": {
                "myapp": {
                    "database": {"host": "localhost", "port": 5432},
                    "debug": True,
                }
            },
        }
        result = extract_settings(data, tool_section="myapp")
        assert result["database"] == {"host": "localhost", "port": 5432}
        assert result["debug"] is True

    def test_custom_root_section(self) -> None:
        data = {
            "settings": {"host": "localhost", "port": 8080, "debug": True},
        }
        result = extract_settings(data, root_section="settings")
        assert result == {"host": "localhost", "port": 8080, "debug": True}

    def test_custom_root_section_with_tool(self) -> None:
        data = {
            "settings": {"host": "localhost"},
            "tool": {"myapp": {"port": 8080}},
        }
        result = extract_settings(data, tool_section="myapp", root_section="settings")
        assert result == {"host": "localhost", "port": 8080}

    def test_custom_root_section_not_found(self) -> None:
        data = {"project": {"name": "myapp"}}
        with pytest.raises(RootSectionNotFoundError):
            extract_settings(data, root_section="missing")

    def test_custom_root_section_no_key_filtering(self) -> None:
        data = {
            "myconfig": {"foo": 1, "bar": "baz", "custom_key": True},
        }
        result = extract_settings(data, root_section="myconfig")
        assert result == {"foo": 1, "bar": "baz", "custom_key": True}
