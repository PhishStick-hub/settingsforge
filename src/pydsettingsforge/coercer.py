"""Coerce env-string values into typed Python objects using a Pydantic model."""

from __future__ import annotations

import json
from typing import Any, get_args, get_origin

from pydantic import BaseModel

from pydsettingsforge.exceptions import SettingsValidationError

_CONTAINER_ORIGINS = (list, set, frozenset, tuple)


def _unwrap_optional(annotation: Any) -> Any:
    args = get_args(annotation)
    if not args or type(None) not in args:
        return annotation
    for a in args:
        if a is not type(None) and get_origin(a) in _CONTAINER_ORIGINS + (dict,):
            return a
    non_none = [a for a in args if a is not type(None)]
    if len(non_none) == 1:
        return non_none[0]
    return annotation


def _split_list(value: str, separator: str) -> list[str]:
    return [item.strip() for item in value.split(separator) if item.strip()]


def _is_list_like(annotation: Any) -> bool:
    return get_origin(_unwrap_optional(annotation)) in _CONTAINER_ORIGINS


def _is_dict(annotation: Any) -> bool:
    return get_origin(_unwrap_optional(annotation)) is dict


def _coerce_list_value(
    value: str,
    list_separator: str,
    field_name: str,
) -> Any:
    stripped = value.strip()
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return _split_list(stripped, list_separator)
        if isinstance(parsed, list):
            return parsed
    return _split_list(stripped, list_separator)


def _coerce_dict_value(
    value: str,
    field_name: str,
) -> Any:
    try:
        return json.loads(value.strip())
    except json.JSONDecodeError as exc:
        raise SettingsValidationError(
            f"Failed to coerce env value for field '{field_name}' "
            f"to dict: invalid JSON: {exc}"
        ) from exc


def _coerce_list_of_models(
    value: str,
    inner_model: type[BaseModel],
    list_separator: str,
    field_name: str,
) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(value.strip())
    except json.JSONDecodeError as exc:
        raise SettingsValidationError(
            f"Failed to coerce env value for field '{field_name}' "
            f"to list[{inner_model.__name__}]: invalid JSON: {exc}"
        ) from exc
    if not isinstance(parsed, list):
        raise SettingsValidationError(
            f"Failed to coerce env value for field '{field_name}': expected JSON list"
        )
    return [
        coerce_env_values(inner_model, item, list_separator=list_separator)
        for item in parsed
    ]


def _coerce_field(
    value: Any,
    annotation: Any,
    list_separator: str,
    field_name: str,
) -> Any:
    inner = _unwrap_optional(annotation)
    origin = get_origin(inner)
    args = get_args(inner)

    if (
        isinstance(inner, type)
        and issubclass(inner, BaseModel)
        and isinstance(value, dict)
    ):
        return coerce_env_values(inner, value, list_separator=list_separator)

    if (
        origin in _CONTAINER_ORIGINS
        and args
        and isinstance(args[0], type)
        and issubclass(args[0], BaseModel)
    ):
        if isinstance(value, str):
            return _coerce_list_of_models(value, args[0], list_separator, field_name)
        return value

    if _is_list_like(annotation):
        if isinstance(value, str):
            return _coerce_list_value(value, list_separator, field_name)
        return value

    if _is_dict(annotation):
        if isinstance(value, str):
            return _coerce_dict_value(value, field_name)
        return value

    return value


def coerce_env_values(
    model_class: type[BaseModel],
    data: dict[str, Any],
    *,
    list_separator: str = ",",
    coerce_env: bool = True,
) -> dict[str, Any]:
    """Pre-process a merged settings dict so list/dict leaf strings become typed values.

    Uses ``model_class.model_fields`` to decide how to interpret each string leaf.
    String values whose target field is a list/set/tuple are split on
    ``list_separator`` (whitespace stripped, empties dropped), or parsed as JSON if
    the value starts with ``[`` (falls back to split on invalid JSON). String
    values whose target field is a ``dict`` are parsed as JSON. String values for
    ``list[BaseModel]`` (or ``set[BaseModel]`` / ``tuple[BaseModel, ...]``) fields
    are parsed as JSON and each element is recursively coerced. Primitive types
    (``int``/``bool``/``float``/``str``) are left untouched — Pydantic handles
    their coercion in ``model_validate``. Optional list/dict fields
    (``list[str] | None``) are detected, including multi-member unions like
    ``list[str] | int | None``. When ``coerce_env`` is False, ``data`` is returned
    as a shallow copy with no coercion applied.

    Extra fields not declared on the model are passed through unchanged.
    """
    if not coerce_env:
        return dict(data)

    result: dict[str, Any] = {}
    known_fields = model_class.model_fields

    for name, field in known_fields.items():
        if name not in data:
            continue
        result[name] = _coerce_field(data[name], field.annotation, list_separator, name)

    for name, value in data.items():
        if name not in known_fields:
            result[name] = value

    return result
