"""Tests for env_reader module."""

from pathlib import Path

import pytest

from pydsettingsforge.env_reader import (
    expand_nested_keys,
    read_env_file,
    read_env_files,
)
from pydsettingsforge.exceptions import EnvFileNotFoundError


class TestReadEnvFile:
    def test_reads_valid_file(self, env_file: Path) -> None:
        result = read_env_file(env_file)
        assert result == {"DEBUG": "true", "LOG_LEVEL": "debug"}

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(EnvFileNotFoundError):
            read_env_file(tmp_path / "nonexistent.env")

    def test_skips_none_values(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("KEY=value\nEMPTY=\n")
        result = read_env_file(env)
        assert "KEY" in result


class TestReadEnvFiles:
    def test_merges_multiple_files(self, tmp_path: Path) -> None:
        first = tmp_path / ".env"
        first.write_text("A=1\nB=2\n")
        second = tmp_path / ".env.local"
        second.write_text("B=override\nC=3\n")

        result = read_env_files([first, second])
        assert result == {"A": "1", "B": "override", "C": "3"}

    def test_empty_list(self) -> None:
        result = read_env_files([])
        assert result == {}


class TestExpandNestedKeys:
    def test_flat_keys(self) -> None:
        result = expand_nested_keys({"DEBUG": "true", "PORT": "8080"})
        assert result == {"debug": "true", "port": "8080"}

    def test_nested_keys(self) -> None:
        result = expand_nested_keys(
            {
                "DATABASE__HOST": "localhost",
                "DATABASE__PORT": "5432",
            }
        )
        assert result == {"database": {"host": "localhost", "port": "5432"}}

    def test_deeply_nested(self) -> None:
        result = expand_nested_keys({"A__B__C": "deep"})
        assert result == {"a": {"b": {"c": "deep"}}}

    def test_custom_separator(self) -> None:
        result = expand_nested_keys({"DATABASE.HOST": "localhost"}, separator=".")
        assert result == {"database": {"host": "localhost"}}

    def test_mixed_flat_and_nested(self) -> None:
        result = expand_nested_keys(
            {
                "DEBUG": "true",
                "DB__HOST": "localhost",
            }
        )
        assert result == {"debug": "true", "db": {"host": "localhost"}}
