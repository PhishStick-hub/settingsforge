"""Custom exceptions for settingsforge."""


class SettingsForgeError(Exception):
    """Base exception for all settingsforge errors."""


class PyprojectNotFoundError(SettingsForgeError):
    """Raised when pyproject.toml cannot be found at the specified path."""

    def __init__(self, path: str) -> None:
        super().__init__(f"pyproject.toml not found at: {path}")


class EnvFileNotFoundError(SettingsForgeError):
    """Raised when a specified .env file does not exist."""

    def __init__(self, path: str) -> None:
        super().__init__(f".env file not found: {path}")


class ToolSectionNotFoundError(SettingsForgeError):
    """Raised when [tool.<name>] section is missing from pyproject.toml."""

    def __init__(self, section: str) -> None:
        super().__init__(f"[tool.{section}] section not found in pyproject.toml")


class RootSectionNotFoundError(SettingsForgeError):
    """Raised when the specified root section is missing from pyproject.toml."""

    def __init__(self, section: str) -> None:
        super().__init__(f"[{section}] section not found in pyproject.toml")


class SettingsValidationError(SettingsForgeError):
    """Raised when the merged settings dictionary fails Pydantic validation."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Settings validation failed: {message}")
