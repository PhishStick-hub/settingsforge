"""Deep-merge dictionaries with override semantics."""

from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries. Values from `override` win on conflict.

    Nested dicts are merged recursively; all other types (including lists)
    are replaced entirely by the override value.
    Returns a new dictionary without mutating inputs.
    """
    result: dict[str, Any] = {**base}

    for key, override_value in override.items():
        base_value = result.get(key)

        if isinstance(base_value, dict) and isinstance(override_value, dict):
            result[key] = deep_merge(base_value, override_value)
        else:
            result[key] = override_value

    return result
