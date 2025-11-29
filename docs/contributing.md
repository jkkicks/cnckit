# Contributing

Thank you for considering contributing to cnckit!

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/jkkicks/cnckit.git
cd cnckit
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e ".[dev]"
```

3. Install pre-commit hooks:

```bash
pre-commit install
```

## Code Quality

### Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=src/cnckit --cov-report=term-missing
```

For HTML coverage report:

```bash
pytest --cov=src/cnckit --cov-report=html
open htmlcov/index.html
```

### Linting

```bash
ruff check .
ruff format .
```

### Type Checking

```bash
mypy src/cnckit
```

### Building Documentation

Preview docs locally:

```bash
mkdocs serve
```

Build static site:

```bash
mkdocs build
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Ensure tests pass and linting is clean
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Guidelines

### Code Style

- Follow PEP 8 (enforced by ruff)
- Use type hints for all public functions
- Write docstrings in Google style

### Testing

- Write tests for all new functionality
- Maintain or improve code coverage
- Tests should be fast and isolated

### Documentation

- Update documentation for user-facing changes
- Include docstrings with examples
- Keep the README in sync

### Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) and [Release Please](https://github.com/googleapis/release-please) for automated versioning and releases.

#### Commit Message Format

```
<type>: <description>

[optional body]

[optional footer(s)]
```

#### Commit Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor (0.1.0 → 0.2.0) |
| `fix` | Bug fix | Patch (0.1.0 → 0.1.1) |
| `docs` | Documentation only | None |
| `style` | Formatting, no code change | None |
| `refactor` | Code change, no new feature or fix | None |
| `test` | Adding or updating tests | None |
| `chore` | Maintenance tasks | None |

#### Breaking Changes

For breaking changes, add `!` after the type or include `BREAKING CHANGE:` in the footer:

```bash
feat!: remove deprecated API endpoints

# or

feat: change authentication flow

BREAKING CHANGE: JWT tokens now required for all endpoints
```

This triggers a major version bump (0.1.0 → 1.0.0).

#### Examples

```bash
feat: add support for tool change macros
fix: resolve race condition in job queue
docs: update API reference for scheduler
refactor: simplify event emitter logic
```

#### Additional Guidelines

- Reference issues where applicable (`fix: resolve login bug (#123)`)
- Keep commits focused and atomic

## Release Process

Releases are automated using [Release Please](https://github.com/googleapis/release-please):

1. **Commits to `main`** are analyzed for conventional commit messages
2. **Release Please creates a PR** that:
   - Bumps the version in `pyproject.toml` and `src/cnckit/__init__.py`
   - Updates the CHANGELOG
3. **Merging the Release PR** creates a GitHub Release
4. **The release triggers** automatic publishing to PyPI

Contributors don't need to worry about versioning - just use conventional commits and the automation handles the rest.

## Architecture Notes

Please review [architecture.md](architecture.md) before making structural changes. The core principles are:

- Keep the core dependency-free
- Integrations are always optional
- Simplicity over features
