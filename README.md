# settingsforge

Load and merge application settings from `pyproject.toml` and `.env` files into validated Pydantic models.

## Features

- Read settings from `pyproject.toml` (`[project]` table + optional `[tool.<name>]` section)
- Read and merge multiple `.env` files with explicit priority ordering
- Nested configuration via `__` separator in `.env` keys (e.g., `DATABASE__HOST=localhost`)
- `.env` values override `pyproject.toml` values
- Validate merged settings against a user-provided Pydantic model
- Clear, specific error messages for missing files, sections, and validation failures

## Installation

```bash
uv add settingsforge
```

## Quick Start

### 1. Define your settings model

```python
from pydantic import BaseModel

class DatabaseConfig(BaseModel):
    host: str
    port: int

class AppSettings(BaseModel):
    name: str
    version: str
    debug: bool = False
    log_level: str = "info"
    database: DatabaseConfig | None = None
```

### 2. Add settings to `pyproject.toml`

```toml
[project]
name = "myapp"
version = "1.0.0"

[tool.myapp]
debug = false
log_level = "info"

[tool.myapp.database]
host = "localhost"
port = 5432
```

### 3. Create `.env` files (optional)

```bash
# .env
DEBUG=true
LOG_LEVEL=debug

# .env.local (overrides .env)
DATABASE__HOST=db.production.com
DATABASE__PORT=3306
```

### 4. Load settings

```python
from settingsforge import load_settings
from myapp.config import AppSettings

settings = load_settings(
    AppSettings,
    tool_section="myapp",
    env_files=[".env", ".env.local"],
)

print(settings.name)            # "myapp"
print(settings.debug)           # True (overridden by .env)
print(settings.database.host)   # "db.production.com" (overridden by .env.local)
```

## Override Priority

Settings are merged in this order (lowest to highest priority):

1. `pyproject.toml` root section fields (default: `[project]`)
2. `pyproject.toml` `[tool.<name>]` section
3. `.env` files (in the order provided in the `env_files` list)
4. OS environment variables (if your model inherits from `pydantic_settings.BaseSettings`)

## Custom Root Section

By default, settingsforge reads from the `[project]` section (filtering to known metadata keys). You can specify a custom root section to read all keys from any TOML table:

```toml
[settings]
host = "localhost"
port = 8080
debug = true
```

```python
settings = load_settings(
    ServerSettings,
    root_section="settings",
)
```

## Extra Fields

By default, Pydantic ignores any fields in your configuration that aren't defined in your model:

```python
class AppSettings(BaseModel):
    debug: bool

# If pyproject.toml has extra fields like "name" or "version",
# they are silently ignored
```

You can control this behavior using Pydantic's `model_config`:

### Forbid Extra Fields (Strict Mode)

Raise an error if unexpected fields are present:

```python
from pydantic import BaseModel, ConfigDict

class StrictSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    debug: bool
    log_level: str

# Raises SettingsValidationError if pyproject.toml contains
# fields not defined in the model
```

### Allow Extra Fields

Accept and store extra fields dynamically:

```python
from pydantic import BaseModel, ConfigDict

class FlexibleSettings(BaseModel):
    model_config = ConfigDict(extra="allow")
    debug: bool

# Extra fields are accessible via settings.model_extra
```

**Note**: This behavior is controlled by your Pydantic model configuration, not by settingsforge.

## API Reference

### `load_settings()`

```python
def load_settings[T: BaseModel](
    model_class: type[T],
    *,
    pyproject_path: Path | str | None = None,
    env_files: list[Path | str] | None = None,
    tool_section: str | None = None,
    root_section: str = "project",
    env_nesting_separator: str = "__",
) -> T
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_class` | `type[BaseModel]` | required | Pydantic model to validate against |
| `pyproject_path` | `Path \| str \| None` | `./pyproject.toml` | Path to `pyproject.toml` |
| `env_files` | `list[Path \| str] \| None` | `None` | Ordered list of `.env` files (later wins) |
| `tool_section` | `str \| None` | `None` | `[tool.<name>]` section to read |
| `root_section` | `str` | `"project"` | Root TOML section to read (custom sections include all keys) |
| `env_nesting_separator` | `str` | `"__"` | Separator for nested `.env` keys |

### Exceptions

| Exception | When |
|-----------|------|
| `PyprojectNotFoundError` | `pyproject.toml` not found |
| `EnvFileNotFoundError` | A specified `.env` file doesn't exist |
| `RootSectionNotFoundError` | Root section is missing |
| `ToolSectionNotFoundError` | `[tool.<name>]` section is missing |
| `SettingsValidationError` | Merged data fails Pydantic validation |

## Development

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

### Setup

```bash
git clone <repo-url>
cd settingsforge
uv sync --all-groups
```

### Commands

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=settingsforge

# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/

# Type check
uv run ty check src/

# All checks
uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run ty check src/ && uv run pytest
```

## Project Structure

```
settingsforge/
├── pyproject.toml
├── uv.lock
├── README.md
├── .gitignore
├── src/
│   └── settingsforge/
│       ├── __init__.py          # Public API: load_settings()
│       ├── constants.py         # Default constants
│       ├── env_reader.py        # .env file parsing and nesting
│       ├── exceptions.py        # Custom exceptions
│       ├── merger.py            # Deep-merge dictionaries
│       ├── toml_reader.py       # pyproject.toml parsing
│       └── validator.py         # Pydantic validation
└── tests/
    ├── conftest.py              # Shared fixtures
    ├── test_env_reader.py
    ├── test_load_settings.py    # Integration tests
    ├── test_merger.py
    ├── test_toml_reader.py
    └── test_validator.py
```

## License

MIT
