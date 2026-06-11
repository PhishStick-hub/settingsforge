"""Tests for toml_reader module."""

from pathlib import Path

import pytest

from pydsettingsforge.exceptions import (
    PyprojectNotFoundError,
    RootSectionNotFoundError,
)
from pydsettingsforge.toml_reader import (
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
    def test_defaults_to_project(self) -> None:
        data = {
            "project": {"name": "myapp", "version": "1.0.0"},
        }
        result = extract_settings(data)
        assert result == {"name": "myapp", "version": "1.0.0"}

    def test_project_filtered_keys(self) -> None:
        data = {
            "project": {
                "name": "myapp",
                "version": "1.0.0",
                "custom": "should-be-excluded",
            },
        }
        result = extract_settings(data)
        assert result == {"name": "myapp", "version": "1.0.0"}
        assert "custom" not in result

    def test_single_tool_section(self) -> None:
        data = {
            "project": {"name": "myapp"},
            "tool": {"myapp": {"debug": False, "log_level": "info"}},
        }
        result = extract_settings(data, toml_sections=["project", "tool.myapp"])
        assert result == {"name": "myapp", "debug": False, "log_level": "info"}

    def test_tool_section_overrides_project(self) -> None:
        data = {
            "project": {"name": "myapp", "version": "1.0.0"},
            "tool": {"myapp": {"version": "2.0.0"}},
        }
        result = extract_settings(data, toml_sections=["project", "tool.myapp"])
        assert result == {"name": "myapp", "version": "2.0.0"}

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
        result = extract_settings(data, toml_sections=["project", "tool.myapp"])
        assert result["database"] == {"host": "localhost", "port": 5432}
        assert result["debug"] is True

    def test_custom_root_section(self) -> None:
        data = {
            "settings": {"host": "localhost", "port": 8080, "debug": True},
        }
        result = extract_settings(data, toml_sections=["settings"])
        assert result == {"host": "localhost", "port": 8080, "debug": True}

    def test_custom_root_section_with_tool(self) -> None:
        data = {
            "settings": {"host": "localhost"},
            "tool": {"myapp": {"port": 8080}},
        }
        result = extract_settings(data, toml_sections=["settings", "tool.myapp"])
        assert result == {"host": "localhost", "port": 8080}

    def test_custom_root_section_not_found(self) -> None:
        data = {"project": {"name": "myapp"}}
        with pytest.raises(RootSectionNotFoundError):
            extract_settings(data, toml_sections=["missing"])

    def test_custom_root_section_no_key_filtering(self) -> None:
        data = {
            "myconfig": {"foo": 1, "bar": "baz", "custom_key": True},
        }
        result = extract_settings(data, toml_sections=["myconfig"])
        assert result == {"foo": 1, "bar": "baz", "custom_key": True}

    def test_nested_root_section(self) -> None:
        data = {
            "autotests": {
                "settings": {"browser": "chromium", "workers": 4, "timeout": 30.0}
            },
        }
        result = extract_settings(data, toml_sections=["autotests.settings"])
        assert result == {"browser": "chromium", "workers": 4, "timeout": 30.0}

    def test_nested_root_section_not_found(self) -> None:
        data = {"project": {"name": "myapp"}}
        with pytest.raises(RootSectionNotFoundError):
            extract_settings(data, toml_sections=["autotests.missing"])

    def test_nested_root_section_intermediate_not_dict(self) -> None:
        data = {"autotests": "not-a-table"}
        with pytest.raises(RootSectionNotFoundError):
            extract_settings(data, toml_sections=["autotests.settings"])

    def test_nested_root_section_with_tool_section(self) -> None:
        data = {
            "autotests": {"settings": {"browser": "chromium", "workers": 2}},
            "tool": {"myapp": {"workers": 8, "timeout": 60.0}},
        }
        result = extract_settings(
            data, toml_sections=["autotests.settings", "tool.myapp"]
        )
        assert result == {"browser": "chromium", "workers": 8, "timeout": 60.0}

    def test_multiple_sections_deep_merge(self) -> None:
        data = {
            "project": {"name": "myapp"},
            "tool": {
                "myapp": {
                    "database": {"host": "localhost", "port": 5432},
                }
            },
        }
        result = extract_settings(
            data,
            toml_sections=[
                "project",
                "tool.myapp",
            ],
        )
        assert result == {
            "name": "myapp",
            "database": {"host": "localhost", "port": 5432},
        }

    def test_section_override_on_conflict(self) -> None:
        data = {
            "defaults": {"host": "localhost", "port": 5432},
            "production": {"host": "prod.local", "pool_size": 10},
        }
        result = extract_settings(data, toml_sections=["defaults", "production"])
        assert result == {
            "host": "prod.local",
            "port": 5432,
            "pool_size": 10,
        }

    def test_four_sections_merged(self) -> None:
        data = {
            "project": {"name": "myapp", "version": "1.0.0"},
            "tool": {"app": {"debug": False, "log_level": "info"}},
            "autotests": {"settings": {"workers": 2}},
        }
        result = extract_settings(
            data,
            toml_sections=[
                "project",
                "tool.app",
                "autotests.settings",
            ],
        )
        assert result == {
            "name": "myapp",
            "version": "1.0.0",
            "debug": False,
            "log_level": "info",
            "workers": 2,
        }
