"""Tests for validator module."""

import pytest
from pydantic import BaseModel

from pydsettingsforge.exceptions import SettingsValidationError
from pydsettingsforge.validator import validate_settings


class SampleSettings(BaseModel):
    name: str
    version: str
    debug: bool = False


class NestedSettings(BaseModel):
    host: str
    port: int


class AppSettings(BaseModel):
    name: str
    database: NestedSettings


class TestValidateSettings:
    def test_valid_data(self) -> None:
        data = {"name": "myapp", "version": "1.0.0"}
        result = validate_settings(SampleSettings, data)
        assert result.name == "myapp"
        assert result.version == "1.0.0"
        assert result.debug is False

    def test_with_defaults(self) -> None:
        data = {"name": "myapp", "version": "1.0.0", "debug": True}
        result = validate_settings(SampleSettings, data)
        assert result.debug is True

    def test_nested_model(self) -> None:
        data = {"name": "myapp", "database": {"host": "localhost", "port": 5432}}
        result = validate_settings(AppSettings, data)
        assert result.database.host == "localhost"
        assert result.database.port == 5432

    def test_validation_error(self) -> None:
        with pytest.raises(SettingsValidationError, match="validation failed"):
            validate_settings(SampleSettings, {"name": "myapp"})

    def test_type_coercion(self) -> None:
        data = {"name": "myapp", "database": {"host": "localhost", "port": "5432"}}
        result = validate_settings(AppSettings, data)
        assert result.database.port == 5432
