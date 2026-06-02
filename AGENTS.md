# AGENTS.md

## What this repo is
- Small Python 3.13+ library (`pydsettingsforge`, currently v0.1.0) — load/merge settings from `pyproject.toml` and `.env` files into a user-supplied Pydantic model.
- Single flat package at `src/pydsettingsforge/`. No monorepo, no sub-packages, no `examples/` or `docs/` directory.
- Package ships type info (`src/pydsettingsforge/py.typed` is present, PEP 561).

## Tooling
- [uv](https://docs.astral.sh/uv/) is the only required tool. `uv_build` is the build backend. No Makefile / nox / tox / poetry.
- Python version is pinned to 3.13 via `.python-version` and `pyproject.toml:requires-python = ">=3.13"`.
- Lint/format: `ruff`. Type check: Astral's `ty` (NOT mypy/pyright).

## Commands (always via `uv run`)

| Task | Command |
|---|---|
| Install (CI) | `uv sync --frozen` |
| Install (local) | `uv sync` |
| Tests | `uv run pytest` |
| Tests + coverage | `uv run pytest --cov=pydsettingsforge` |
| Single test | `uv run pytest tests/test_load_settings.py::TestLoadSettings::test_env_overrides_toml -v` |
| Lint | `uv run ruff check src/ tests/` |
| Format | `uv run ruff format src/ tests/` (add `--check` to verify) |
| Type check | `uv run ty check src/` |
| All gates (CI order) | `uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run ty check src/ && uv run pytest` |

CI runs `lint`, `typecheck`, `test` as three independent jobs — that order is the required gate order in `branch-protection-rules.json` (`strict: true`).

## Gotchas an agent will miss

- **`ty` only typechecks `src/`, not `tests/`.** `tests/` is intentionally untyped. Do not add tests to the typecheck command.
- **`.env` keys are lowercased** by `env_reader.expand_nested_keys` (`src/pydsettingsforge/env_reader.py:48`). Pydantic field names must match the lowercased form, e.g. `DATABASE__HOST` → `database.host`.
- **Default root section filters keys.** When `root_section="project"` (the default), `toml_reader.extract_settings` only keeps the metadata keys in `TOP_LEVEL_KEYS` (`src/pydsettingsforge/toml_reader.py:18`: `name`, `version`, `description`, `requires-python`, `readme`, `authors`). Custom root sections include all keys unfiltered.
- **`deep_merge` replaces lists** instead of concatenating (`src/pydsettingsforge/merger.py`). Don't expect `[1,2] + override [3]` → `[1,2,3]`.
- **`__version__` lives in `src/pydsettingsforge/__init__.py:8`** and MUST match `pyproject.toml:project.version`. Both are updated by `python-semantic-release` — do not bump them by hand.
- **Override priority** (lowest → highest): `[project]` filtered fields → `[tool.<name>]` → `.env` files in the order given (later wins) → OS env (only if the Pydantic model inherits from `pydantic_settings.BaseSettings`).
- **Public API surface is narrow.** `load_settings`, `coerce_env_values`, and the exception classes re-exported in `src/pydsettingsforge/__init__.py:29-38` are public. `env_reader`, `toml_reader`, `merger`, `validator`, and `coercer` (other than the re-exported `coerce_env_values`) are internal — don't import from them in user-facing docs.
- **Env-string coercion is opt-in by default.** `load_settings` runs `coerce_env_values` (`src/pydsettingsforge/coercer.py`) after merging unless `coerce_env=False`. The coercer splits `list`/`set`/`tuple`/`frozenset` strings on `list_separator` (default `,`) or parses JSON if the value starts with `[`; dict strings are always JSON-parsed; `list[BaseModel]` / `set[BaseModel]` / `tuple[BaseModel, ...]` are JSON-parsed and each element is recursively coerced. JSON parse failure on a list-like field falls back to splitting; JSON parse failure on a dict or `list[BaseModel]` field raises `SettingsValidationError`.

## Workflow
- Branch from `main`; PRs target `main`. Branch protection requires all three CI jobs green and an up-to-date branch (`strict: true`).
- **Conventional Commits are mandatory** (`CONTRIBUTING.md`). `python-semantic-release` parses every commit on `main` to bump the version and update `CHANGELOG.md` — vague messages break releases.
- `tool.semantic_release.major_on_zero = true` in `pyproject.toml` — a `BREAKING CHANGE:` while on `0.x.y` triggers a major bump to `1.0.0`.
- Dependabot opens weekly PRs for `pip` and `github-actions` ecosystems (`.github/dependabot.yml`); keep an eye on stale PRs.
- Release flow (`.github/workflows/release.yml`): PSR step runs with `build: false`; a separate job then runs `uv build` and uploads `dist/`; `publish` uses `environment: pypi` + `PYPI_API_TOKEN`. Local release work is not needed — push to `main` and let CI do it.

## Tests
- Pytest config: `testpaths = ["tests"]`, `addopts = "-v --tb=short"`.
- Shared fixtures in `tests/conftest.py`: `tmp_project` (writes a baseline `pyproject.toml`), `env_file`, `nested_env_file`. Use them rather than hand-rolling fixtures in new test files.
- `tests/test_load_settings.py` is the integration suite; the other `test_*.py` files mirror the source module they cover.
- No external services, no network, no DB. Everything runs in `tmp_path`.

## Style / house rules
- No code comments unless asked. Existing modules are clean and self-documenting; follow that.
- Keep public API stable — adding new public symbols requires updating `__all__` in `__init__.py` and adding tests in `test_load_settings.py` for any new `load_settings` parameter.
- `CHANGELOG.md` is regenerated by PSR on release. Don't hand-edit it.
