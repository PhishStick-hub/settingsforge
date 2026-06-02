"""Read and parse .env files."""

from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from pydsettingsforge.constants import ENV_NESTING_SEPARATOR
from pydsettingsforge.exceptions import EnvFileNotFoundError


def read_env_file(path: Path) -> dict[str, str]:
    """Parse a single .env file and return key-value pairs.

    Raises EnvFileNotFoundError if the file does not exist.
    """
    if not path.is_file():
        raise EnvFileNotFoundError(str(path))

    values = dotenv_values(path)
    return {k: v for k, v in values.items() if v is not None}


def read_env_files(paths: list[Path]) -> dict[str, str]:
    """Read multiple .env files and merge them.

    Files are processed in order; later files override earlier ones.
    """
    merged: dict[str, str] = {}
    for path in paths:
        merged.update(read_env_file(path))
    return merged


def expand_nested_keys(
    flat: dict[str, str],
    separator: str = ENV_NESTING_SEPARATOR,
) -> dict[str, Any]:
    """Convert flat keys with a nesting separator into a nested dictionary.

    Example: {"DB__HOST": "localhost"} -> {"db": {"host": "localhost"}}

    Keys are lowercased to match typical Pydantic field naming conventions.
    """
    result: dict[str, Any] = {}

    for key, value in flat.items():
        parts = key.lower().split(separator)
        current = result

        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result
