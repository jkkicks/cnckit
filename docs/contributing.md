# Contributing

Thank you for considering contributing to cnckit!

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/jacobm/cnckit.git
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

- Use clear, descriptive commit messages
- Reference issues where applicable
- Keep commits focused and atomic

## Architecture Notes

Please review [architecture.md](architecture.md) before making structural changes. The core principles are:

- Keep the core dependency-free
- Integrations are always optional
- Simplicity over features
