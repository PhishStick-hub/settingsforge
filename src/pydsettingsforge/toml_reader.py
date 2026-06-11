"""Read and extract settings from pyproject.toml."""

import tomllib
from pathlib import Path
from typing import Any

from pydsettingsforge.constants import DEFAULT_ROOT_SECTION, DEFAULT_TOML_SECTIONS
from pydsettingsforge.exceptions import (
    PyprojectNotFoundError,
    RootSectionNotFoundError,
)
from pydsettingsforge.merger import deep_merge

TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "name",
        "version",
        "description",
        "requires-python",
        "readme",
        "authors",
    }
)


def resolve_pyproject_path(path: Path | None = None) -> Path:
    """Resolve the path to pyproject.toml.

    If no path is given, looks in the current working directory.
    """
    if path is None:
        return Path.cwd() / "pyproject.toml"
    return path.resolve()


def read_pyproject(path: Path) -> dict[str, Any]:
    """Parse pyproject.toml and return its contents as a dictionary."""
    if not path.is_file():
        raise PyprojectNotFoundError(str(path))

    with path.open("rb") as f:
        return tomllib.load(f)


def _resolve_nested_key(data: dict[str, Any], path: str) -> dict[str, Any]:
    """Walk a dotted path into a nested dict structure.

    ``path`` is a dot-separated TOML section path such as ``"project"``,
    ``"tool.myapp"``, or ``"autotests.settings"``.
    Raises RootSectionNotFoundError if any segment is missing or not a dict.
    """
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            raise RootSectionNotFoundError(path)
        current = current[part]
    if not isinstance(current, dict):
        raise RootSectionNotFoundError(path)
    return current


def extract_settings(
    pyproject_data: dict[str, Any],
    toml_sections: list[str] | None = None,
) -> dict[str, Any]:
    """Extract settings from one or more pyproject.toml sections.

    Each entry in ``toml_sections`` is a dot-separated path into the parsed
    TOML data (e.g. ``"project"``, ``"tool.myapp"``,
    ``"autotests.settings"``).  Sections are merged left-to-right — later
    sections override earlier ones on key conflict.

    When ``toml_sections`` is ``None``, defaults to ``["project"]``.

    When the section path is exactly ``"project"``, only known PEP 621
    metadata keys (``name``, ``version``, ``description``,
    ``requires-python``, ``readme``, ``authors``) are included.
    All other sections include every key unfiltered.
    """
    if toml_sections is None:
        toml_sections = DEFAULT_TOML_SECTIONS

    result: dict[str, Any] = {}
    for section in toml_sections:
        section_data = _resolve_nested_key(pyproject_data, section)
        if section == DEFAULT_ROOT_SECTION:
            section_data = {
                k: v for k, v in section_data.items() if k in TOP_LEVEL_KEYS
            }
        result = deep_merge(result, section_data)

    return result
