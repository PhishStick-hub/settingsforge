"""Coerce env-string values into typed Python objects using a Pydantic model."""

from __future__ import annotations

import json
from typing import Any, get_args, get_origin

from pydantic import BaseModel

from pydsettingsforge.exceptions import SettingsValidationError


def _unwrap_optional(annotation: Any) -> Any:
    args = get_args(annotation)
    if args and type(None) in args:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return annotation


def _split_list(value: str, separator: str) -> list[str]:
    return [item.strip() for item in value.split(separator) if item.strip()]


def _is_list_like(annotation: Any) -> bool:
    return get_origin(_unwrap_optional(annotation)) in (list, set, tuple, frozenset)


def _is_dict(annotation: Any) -> bool:
    return get_origin(_unwrap_optional(annotation)) is dict


def _coerce_leaf(
    value: Any,
    annotation: Any,
    list_separator: str,
    field_name: str,
) -> Any:
    if not isinstance(value, str):
        return value

    if _is_list_like(annotation):
        stripped = value.strip()
        if stripped.startswith(("[", "{")):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise SettingsValidationError(
                    f"Failed to coerce env value for field '{field_name}' "
                    f"to list-like: invalid JSON: {exc}"
                ) from exc
        return _split_list(stripped, list_separator)

    if _is_dict(annotation):
        stripped = value.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise SettingsValidationError(
                f"Failed to coerce env value for field '{field_name}' "
                f"to dict: invalid JSON: {exc}"
            ) from exc

    return value


def coerce_env_values(
    model_class: type[BaseModel],
    data: dict[str, Any],
    *,
    list_separator: str = ",",
) -> dict[str, Any]:
    """Pre-process a merged settings dict so list/dict leaf strings become typed values.

    Uses ``model_class.model_fields`` to decide how to interpret each string leaf.
    String values whose target field is a list/set/tuple are split on
    ``list_separator`` (whitespace stripped, empties dropped), or parsed as JSON if
    the value starts with ``[`` or ``{``. String values whose target field is a
    ``dict`` are parsed as JSON. Primitive types (``int``/``bool``/``float``/``str``)
    are left untouched — Pydantic handles their coercion in ``model_validate``.
    Optional list/dict fields (``list[str] | None``) are detected.

    Extra fields not declared on the model are passed through unchanged.
    """
    result: dict[str, Any] = {}
    known_fields = model_class.model_fields

    for name, field in known_fields.items():
        if name not in data:
            continue
        value = data[name]
        annotation = field.annotation

        if (
            isinstance(annotation, type)
            and issubclass(annotation, BaseModel)
            and isinstance(value, dict)
        ):
            result[name] = coerce_env_values(
                annotation, value, list_separator=list_separator
            )
        else:
            result[name] = _coerce_leaf(value, annotation, list_separator, name)

    for name, value in data.items():
        if name not in known_fields:
            result[name] = value

    return result
