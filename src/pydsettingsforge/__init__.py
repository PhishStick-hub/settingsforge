"""pydsettingsforge — Load and merge settings from pyproject.toml and .env files."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel

__version__ = "2.0.1"

from pydsettingsforge.coercer import coerce_env_values
from pydsettingsforge.constants import DEFAULT_TOML_SECTIONS, ENV_NESTING_SEPARATOR
from pydsettingsforge.env_reader import expand_nested_keys, read_env_files
from pydsettingsforge.exceptions import (
    EnvFileNotFoundError,
    PyprojectNotFoundError,
    RootSectionNotFoundError,
    SettingsForgeError,
    SettingsValidationError,
    ToolSectionNotFoundError,
)
from pydsettingsforge.merger import deep_merge
from pydsettingsforge.toml_reader import (
    extract_settings,
    read_pyproject,
    resolve_pyproject_path,
)
from pydsettingsforge.validator import validate_settings

__all__ = [
    "EnvFileNotFoundError",
    "PyprojectNotFoundError",
    "RootSectionNotFoundError",
    "SettingsForgeError",
    "SettingsValidationError",
    "ToolSectionNotFoundError",
    "coerce_env_values",
    "load_settings",
]


def load_settings[T: BaseModel](
    model_class: type[T],
    *,
    pyproject_path: Path | str | None = None,
    env_files: list[Path | str] | None = None,
    toml_sections: list[str] | None = None,
    env_nesting_separator: str = ENV_NESTING_SEPARATOR,
    coerce_env: bool = True,
    list_separator: str = ",",
) -> T:
    """Load, merge, and validate application settings.

    Reads settings from one or more sections of pyproject.toml, merges them
    left-to-right (later sections override earlier), then merges with .env files
    (later files override earlier), and validates against a Pydantic model.

    Override priority (lowest to highest):
        1. pyproject.toml sections (in list order)
        2. .env files (in list order)
        3. OS environment variables (handled by pydantic-settings if the model
           inherits from BaseSettings)

    Args:
        model_class: A Pydantic BaseModel subclass defining the expected settings.
        pyproject_path: Path to pyproject.toml. Defaults to ./pyproject.toml.
        env_files: Ordered list of .env file paths. Later files override earlier.
        toml_sections: Ordered list of dot-separated TOML section paths
            (e.g. ``["project", "tool.myapp"]``). Later sections override earlier.
            When ``"project"`` is listed, only known PEP 621 metadata keys
            (name, version, description, requires-python, readme, authors)
            are included. Defaults to ``["project"]``.
        env_nesting_separator: Separator for nested keys in .env files
            (default: ``"__"``).
        coerce_env: When True (default), string values for list, set, tuple, and
            dict fields are parsed before Pydantic validation: list-like fields
            are split on ``list_separator`` (or parsed as JSON if the value starts
            with ``[`` or ``{``), and dict fields are parsed as JSON. Set to False
            to keep raw string passthrough.
        list_separator: Separator used to split string values for list-like
            fields when ``coerce_env`` is True (default: ``,``).

    Returns:
        A validated instance of model_class.

    Raises:
        PyprojectNotFoundError: If pyproject.toml is not found.
        EnvFileNotFoundError: If a specified .env file does not exist.
        RootSectionNotFoundError: If a requested TOML section is missing.
        SettingsValidationError: If the merged data fails Pydantic validation.
    """
    resolved_pyproject = resolve_pyproject_path(
        Path(pyproject_path) if pyproject_path else None
    )
    pyproject_data = read_pyproject(resolved_pyproject)
    toml_settings = extract_settings(
        pyproject_data, toml_sections or DEFAULT_TOML_SECTIONS
    )

    env_settings: dict[str, Any] = {}
    if env_files:
        resolved_env_paths = [Path(p) for p in env_files]
        flat_env = read_env_files(resolved_env_paths)
        env_settings = expand_nested_keys(flat_env, env_nesting_separator)

    merged = deep_merge(toml_settings, env_settings)

    if coerce_env:
        merged = coerce_env_values(model_class, merged, list_separator=list_separator)

    return validate_settings(model_class, merged)
