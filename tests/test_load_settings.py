"""Integration tests for load_settings."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from pydsettingsforge import load_settings
from pydsettingsforge.exceptions import (
    EnvFileNotFoundError,
    PyprojectNotFoundError,
    RootSectionNotFoundError,
    SettingsValidationError,
    ToolSectionNotFoundError,
)


class DatabaseConfig(BaseModel):
    host: str
    port: int


class AppSettings(BaseModel):
    name: str
    version: str
    debug: bool = False
    log_level: str = "info"
    database: DatabaseConfig | None = None


class TestLoadSettings:
    def test_toml_only(self, tmp_project: Path) -> None:
        pyproject = tmp_project / "pyproject.toml"
        result = load_settings(
            AppSettings,
            pyproject_path=pyproject,
            tool_section="myapp",
        )
        assert result.name == "myapp"
        assert result.version == "1.0.0"
        assert result.debug is False
        assert result.log_level == "info"

    def test_env_overrides_toml(self, tmp_project: Path, env_file: Path) -> None:
        pyproject = tmp_project / "pyproject.toml"
        result = load_settings(
            AppSettings,
            pyproject_path=pyproject,
            env_files=[env_file],
            tool_section="myapp",
        )
        assert result.debug is True
        assert result.log_level == "debug"

    def test_nested_env_overrides_toml(
        self, tmp_project: Path, nested_env_file: Path
    ) -> None:
        pyproject = tmp_project / "pyproject.toml"
        result = load_settings(
            AppSettings,
            pyproject_path=pyproject,
            env_files=[nested_env_file],
            tool_section="myapp",
        )
        assert result.database is not None
        assert result.database.host == "db.example.com"
        assert result.database.port == 3306

    def test_multiple_env_files_last_wins(self, tmp_project: Path) -> None:
        pyproject = tmp_project / "pyproject.toml"
        first_env = tmp_project / ".env"
        first_env.write_text("DEBUG=true\nLOG_LEVEL=warn\n")
        second_env = tmp_project / ".env.local"
        second_env.write_text("LOG_LEVEL=error\n")

        result = load_settings(
            AppSettings,
            pyproject_path=pyproject,
            env_files=[first_env, second_env],
            tool_section="myapp",
        )
        assert result.debug is True
        assert result.log_level == "error"

    def test_pyproject_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(PyprojectNotFoundError):
            load_settings(AppSettings, pyproject_path=tmp_path / "missing.toml")

    def test_env_file_not_found(self, tmp_project: Path) -> None:
        pyproject = tmp_project / "pyproject.toml"
        with pytest.raises(EnvFileNotFoundError):
            load_settings(
                AppSettings,
                pyproject_path=pyproject,
                env_files=[tmp_project / "missing.env"],
            )

    def test_tool_section_not_found(self, tmp_project: Path) -> None:
        pyproject = tmp_project / "pyproject.toml"
        with pytest.raises(ToolSectionNotFoundError):
            load_settings(
                AppSettings,
                pyproject_path=pyproject,
                tool_section="nonexistent",
            )

    def test_validation_error(self, tmp_project: Path) -> None:
        pyproject = tmp_project / "pyproject.toml"

        class StrictSettings(BaseModel):
            required_field: str

        with pytest.raises(SettingsValidationError):
            load_settings(StrictSettings, pyproject_path=pyproject)

    def test_no_tool_section(self, tmp_project: Path) -> None:
        pyproject = tmp_project / "pyproject.toml"

        class MinimalSettings(BaseModel):
            name: str
            version: str

        result = load_settings(MinimalSettings, pyproject_path=pyproject)
        assert result.name == "myapp"
        assert result.version == "1.0.0"

    def test_string_paths(self, tmp_project: Path, env_file: Path) -> None:
        result = load_settings(
            AppSettings,
            pyproject_path=str(tmp_project / "pyproject.toml"),
            env_files=[str(env_file)],
            tool_section="myapp",
        )
        assert result.name == "myapp"
        assert result.debug is True

    def test_custom_root_section(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[settings]\nhost = "localhost"\nport = 8080\ndebug = true\n'
        )

        class ServerSettings(BaseModel):
            host: str
            port: int
            debug: bool = False

        result = load_settings(
            ServerSettings,
            pyproject_path=pyproject,
            root_section="settings",
        )
        assert result.host == "localhost"
        assert result.port == 8080
        assert result.debug is True

    def test_custom_root_section_not_found(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myapp"\n')

        class MinimalSettings(BaseModel):
            name: str

        with pytest.raises(RootSectionNotFoundError):
            load_settings(
                MinimalSettings,
                pyproject_path=pyproject,
                root_section="missing",
            )
