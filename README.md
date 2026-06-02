# pydsettingsforge

Load and merge application settings from `pyproject.toml` and `.env` files into validated Pydantic models.

## Features

- Read settings from `pyproject.toml` (`[project]` table + optional `[tool.<name>]` section)
- Read and merge multiple `.env` files with explicit priority ordering
- Nested configuration via `__` separator in `.env` keys (e.g., `DATABASE__HOST=localhost`)
- Automatic coercion of `.env` list and dict values from Pydantic model hints
- `.env` values override `pyproject.toml` values
- Validate merged settings against a user-provided Pydantic model
- Clear, specific error messages for missing files, sections, and validation failures

## Installation

```bash
uv add pydsettingsforge
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
from pydsettingsforge import load_settings
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

## Lists and Dicts in .env

`.env` values are always strings, but your Pydantic model knows the target type. pydsettingsforge uses those hints to parse list-like and dict fields automatically:

```python
class AppSettings(BaseModel):
    allowed_hosts: list[str]
    ports: list[int]
    features: dict[str, int]
```

```bash
# .env
ALLOWED_HOSTS=api.example.com,web.example.com
PORTS=80,443,5432
FEATURES={"timeout": 30, "retries": 3}
```

```python
settings = load_settings(AppSettings, env_files=[".env"])
settings.allowed_hosts  # ["api.example.com", "web.example.com"]
settings.ports          # [80, 443, 5432]  (Pydantic coerces each element)
settings.features       # {"timeout": 30, "retries": 3}
```

**Rules:**

- **List-like fields** (`list`, `set`, `tuple`, `frozenset`): split on `,` by default, whitespace stripped, empty parts dropped. If the value starts with `[`, it is parsed as JSON instead; on invalid JSON the value is split as a fallback.
- **Dict fields**: parsed as JSON.
- **Per-element types** (e.g. `list[int]`, `list[bool]`): the list is split into strings, then Pydantic coerces each element during model validation.
- **Optional list/dict fields** (`list[str] | None`) are detected. Multi-member unions like `list[str] | int | None` also detect the list member.
- **Nested model lists** (`list[BaseModel]`, `set[BaseModel]`, `tuple[BaseModel, ...]`): the value must be a JSON list; each element is recursively coerced, so child `list` / `dict` fields inside the model are parsed the same way as top-level fields.
- **Custom separator**: pass `list_separator=";"` to `load_settings` to split on a different character.
- **Opt out**: pass `coerce_env=False` to keep raw string passthrough (the prior behavior).

If a value cannot be parsed (e.g. malformed JSON for a dict field or a `list[BaseModel]` field), a `SettingsValidationError` is raised with the offending field name.

```python
class Server(BaseModel):
    host: str
    tags: list[str]

class AppSettings(BaseModel):
    servers: list[Server]
```

```bash
SERVERS=[{"host": "a.example.com", "tags": "primary,public"}, {"host": "b.example.com", "tags": "backup"}]
```

```python
settings.servers[0].host  # "a.example.com"
settings.servers[0].tags  # ["primary", "public"]  (child list coerced too)
```

## Custom Root Section

By default, pydsettingsforge reads from the `[project]` section (filtering to known metadata keys). You can specify a custom root section to read all keys from any TOML table:

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

**Note**: This behavior is controlled by your Pydantic model configuration, not by pydsettingsforge.

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
    coerce_env: bool = True,
    list_separator: str = ",",
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
| `coerce_env` | `bool` | `True` | Parse list/dict string values via the model hints before validation |
| `list_separator` | `str` | `","` | Separator for list-like fields when `coerce_env` is enabled |

### `coerce_env_values()`

```python
def coerce_env_values(
    model_class: type[BaseModel],
    data: dict[str, Any],
    *,
    list_separator: str = ",",
    coerce_env: bool = True,
) -> dict[str, Any]
```

The same list/dict coercion that `load_settings` runs after merging, exposed as a standalone helper. Use it when you build the settings dict yourself (e.g. from a custom config source) and want the same string-to-typed-value behavior before handing the dict to Pydantic.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_class` | `type[BaseModel]` | required | Pydantic model used to interpret each leaf |
| `data` | `dict[str, Any]` | required | The dict to coerce (not mutated) |
| `list_separator` | `str` | `","` | Separator for list-like fields |
| `coerce_env` | `bool` | `True` | Set to `False` to return a shallow copy with no coercion |

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
cd pydsettingsforge
uv sync --all-groups
```

### Commands

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=pydsettingsforge

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
pydsettingsforge/
├── pyproject.toml
├── uv.lock
├── README.md
├── .gitignore
├── src/
│   └── pydsettingsforge/
│       ├── __init__.py          # Public API: load_settings(), coerce_env_values()
│       ├── constants.py         # Default constants
│       ├── coercer.py           # List/dict coercion from Pydantic hints
│       ├── env_reader.py        # .env file parsing and nesting
│       ├── exceptions.py        # Custom exceptions
│       ├── merger.py            # Deep-merge dictionaries
│       ├── toml_reader.py       # pyproject.toml parsing
│       └── validator.py         # Pydantic validation
└── tests/
    ├── conftest.py              # Shared fixtures
    ├── test_coercer.py
    ├── test_env_reader.py
    ├── test_load_settings.py    # Integration tests
    ├── test_merger.py
    ├── test_toml_reader.py
    └── test_validator.py
```

## License

MIT
