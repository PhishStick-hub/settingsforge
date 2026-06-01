"""Validate merged settings against a user-provided Pydantic model."""

from typing import Any

from pydantic import BaseModel, ValidationError

from settingsforge.exceptions import SettingsValidationError


def validate_settings[T: BaseModel](
    model_class: type[T],
    data: dict[str, Any],
) -> T:
    """Validate a settings dictionary against a Pydantic model.

    Returns an instance of the model if validation passes.
    Raises SettingsValidationError with details on failure.
    """
    try:
        return model_class.model_validate(data)
    except ValidationError as exc:
        raise SettingsValidationError(str(exc)) from exc
