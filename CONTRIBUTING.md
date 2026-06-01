# Contributing to settingsforge

Thank you for your interest in contributing to settingsforge! This document provides guidelines and instructions for contributing.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/PhishStick-hub/settingsforge.git
   cd settingsforge
   ```

2. Install dependencies with [uv](https://docs.astral.sh/uv/):
   ```bash
   uv sync
   ```

3. Run tests:
   ```bash
   uv run pytest
   ```

4. Run tests with coverage:
   ```bash
   uv run pytest --cov=settingsforge
   ```

## Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Linting
uv run ruff check src/ tests/

# Formatting
uv run ruff format src/ tests/

# Type checking
uv run ty check src/
```

## Commit Message Guidelines

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog generation. Your commit messages must follow this format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature (triggers minor version bump)
- **fix**: A bug fix (triggers patch version bump)
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files

### Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the commit body or append `!` after the type:

```
feat!: remove deprecated load_config function

BREAKING CHANGE: The load_config function has been removed.
Use load_settings instead.
```

### Examples

```bash
feat: add support for YAML configuration files
fix: handle missing .env file gracefully
docs: update README with new API examples
test: add integration tests for nested env vars
refactor: simplify merge logic in merger.py
chore: update dependencies
```

## Pull Request Process

1. Fork the repository and create your branch from `main`
2. If you've added code, add tests
3. Ensure all tests pass and code quality checks succeed
4. Update documentation as needed
5. Submit a pull request

## Release Process

Releases are automated using [python-semantic-release](https://python-semantic-release.readthedocs.io/):

1. When a PR is merged to `main`, the release workflow analyzes commit messages
2. Version is bumped according to conventional commits (major/minor/patch)
3. CHANGELOG.md is updated automatically
4. A new GitHub Release is created
5. Package is published to PyPI via Trusted Publishing (OIDC)

No manual intervention is required for releases.

## Questions?

Feel free to open an issue if you have questions or need clarification.
