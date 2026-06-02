"""Read and extract settings from pyproject.toml."""

import tomllib
from pathlib import Path
from typing import Any

from pydsettingsforge.constants import (
    DEFAULT_PYPROJECT_FILENAME,
    DEFAULT_ROOT_SECTION,
    TOOL_SECTION_PREFIX,
)
from pydsettingsforge.exceptions import (
    PyprojectNotFoundError,
    RootSectionNotFoundError,
    ToolSectionNotFoundError,
)

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
        return Path.cwd() / DEFAULT_PYPROJECT_FILENAME
    return path.resolve()


def read_pyproject(path: Path) -> dict[str, Any]:
    """Parse pyproject.toml and return its contents as a dictionary."""
    if not path.is_file():
        raise PyprojectNotFoundError(str(path))

    with path.open("rb") as f:
        return tomllib.load(f)


def extract_settings(
    pyproject_data: dict[str, Any],
    tool_section: str | None = None,
    root_section: str = DEFAULT_ROOT_SECTION,
) -> dict[str, Any]:
    """Extract settings from parsed pyproject.toml data.

    Returns fields from the root section merged with an optional [tool.<name>] section.
    When root_section is "project" (default), only known metadata keys are included.
    For custom root sections, all keys are included without filtering.
    """
    if root_section not in pyproject_data:
        raise RootSectionNotFoundError(root_section)

    root_table: dict[str, Any] = pyproject_data[root_section]

    if root_section == DEFAULT_ROOT_SECTION:
        top_level = {k: v for k, v in root_table.items() if k in TOP_LEVEL_KEYS}
    else:
        top_level = dict(root_table)

    if tool_section is None:
        return top_level

    tool_table = pyproject_data.get(TOOL_SECTION_PREFIX, {})
    if tool_section not in tool_table:
        raise ToolSectionNotFoundError(tool_section)

    section_data = tool_table[tool_section]
    return {**top_level, **section_data}
