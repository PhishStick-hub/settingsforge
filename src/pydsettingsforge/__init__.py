"""pydsettingsforge — Load and merge settings from pyproject.toml and .env files."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel

__version__ = "0.1.0"

from pydsettingsforge.coercer import coerce_env_values
from pydsettingsforge.constants import DEFAULT_ROOT_SECTION, ENV_NESTING_SEPARATOR
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
    tool_section: str | None = None,
    root_section: str = DEFAULT_ROOT_SECTION,
    env_nesting_separator: str = ENV_NESTING_SEPARATOR,
    coerce_env: bool = True,
    list_separator: str = ",",
) -> T:
    """Load, merge, and validate application settings.

    Reads settings from pyproject.toml (root section + optional [tool.<name>] section),
    merges with .env files (later files override earlier ones), and validates
    the result against a user-provided Pydantic model.

    Override priority (lowest to highest):
        1. pyproject.toml root section fields
        2. pyproject.toml [tool.<name>] section
        3. .env files (in list order)
        4. OS environment variables (handled by pydantic-settings if the model
           inherits from BaseSettings)

    Args:
        model_class: A Pydantic BaseModel subclass defining the expected settings.
        pyproject_path: Path to pyproject.toml. Defaults to ./pyproject.toml.
        env_files: Ordered list of .env file paths. Later files override earlier.
        tool_section: Name of the [tool.<name>] section to read from pyproject.toml.
        root_section: Root TOML section to read (default: "project").
            When "project", only known metadata keys are included.
            Custom sections include all keys unfiltered.
        env_nesting_separator: Separator for nested keys in .env files (default: "__").
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
        RootSectionNotFoundError: If the root section is missing.
        ToolSectionNotFoundError: If the [tool.<name>] section is missing.
        SettingsValidationError: If the merged data fails Pydantic validation.
    """
    resolved_pyproject = resolve_pyproject_path(
        Path(pyproject_path) if pyproject_path else None
    )
    pyproject_data = read_pyproject(resolved_pyproject)
    toml_settings = extract_settings(pyproject_data, tool_section, root_section)

    env_settings: dict[str, Any] = {}
    if env_files:
        resolved_env_paths = [Path(p) for p in env_files]
        flat_env = read_env_files(resolved_env_paths)
        env_settings = expand_nested_keys(flat_env, env_nesting_separator)

    merged = deep_merge(toml_settings, env_settings)

    if coerce_env:
        merged = coerce_env_values(model_class, merged, list_separator=list_separator)

    return validate_settings(model_class, merged)
