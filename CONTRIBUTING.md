# Contributing to llm-discovery

Thank you for your interest in contributing to llm-discovery! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/llm-discovery.git
   cd llm-discovery
   ```

3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/drillan/llm-discovery.git
   ```

## Development Setup

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Install dependencies with development extras
uv sync --all-extras

# Verify installation
uv run pytest --version
uv run ruff --version
uv run mypy --version
```

### Environment Variables

Create a `.env` file for local development:

```bash
# OpenAI (optional)
export OPENAI_API_KEY="sk-..."

# Google AI Studio (optional)
export GOOGLE_API_KEY="AIza..."

# Google Vertex AI (optional)
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Cache directory (optional, defaults to ~/.cache/llm-discovery)
export LLM_DISCOVERY_CACHE_DIR="/path/to/cache"
```

## Development Workflow

### Creating a Branch

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
```

### Making Changes

1. Make your changes in your feature branch
2. Add tests for new functionality
3. Update documentation as needed
4. Run the test suite and quality checks (see below)

### Quality Checks

Before committing, ensure all quality checks pass:

```bash
# Run linting
uv run ruff check llm_discovery/

# Run type checking
uv run mypy llm_discovery/

# Run tests with coverage
uv run pytest tests/ --cov=llm_discovery --cov-report=term-missing

# Run all checks together
uv run ruff check llm_discovery/ && \
uv run mypy llm_discovery/ && \
uv run pytest tests/ --cov=llm_discovery --cov-fail-under=90
```

## Code Standards

### Python Style

- **Python Version**: Python 3.13+
- **Line Length**: 100 characters (enforced by Ruff)
- **Type Hints**: Required for all functions and methods
- **Docstrings**: Required for all public functions, classes, and modules

### Code Principles

#### Primary Data Non-Assumption Principle

**Never hardcode primary data sources.** All configuration values, API keys, and parameters must be:

- Retrieved from environment variables
- Loaded from configuration files
- Passed as explicit parameters

**Prohibited:**
```python
# ❌ Bad - hardcoded value
timeout = 30
api_key = "sk-..."
```

**Required:**
```python
# ✅ Good - explicit configuration
timeout = int(os.environ["API_TIMEOUT"])
api_key = os.environ["OPENAI_API_KEY"]
```

#### Error Handling

- Use **fail-fast** approach - detect and report errors immediately
- Provide **clear error messages** with suggested solutions
- Use **custom exceptions** from `llm_discovery.exceptions`
- Chain exceptions using `from e` for traceability

#### Datetime Handling

- Always use **UTC timezone**: `datetime.now(UTC)`
- Use Python 3.13's `datetime.UTC` (not `timezone.utc`)
- Validate and convert all datetime inputs to UTC

### Testing Standards

- **Coverage**: Maintain 90%+ test coverage
- **Test Types**: Write unit, integration, and CLI tests
- **Markers**: Use pytest markers (`unit`, `integration`, `contract`, `edge`)
- **Fixtures**: Use shared fixtures from `tests/conftest.py`

### Documentation

- Update **README.md** for user-facing changes
- Update **CHANGELOG.md** following Keep a Changelog format
- Add **docstrings** to all public APIs
- Include **type hints** in function signatures

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=llm_discovery

# Run specific test file
uv run pytest tests/test_models.py

# Run specific test class
uv run pytest tests/test_models.py::TestModel

# Run with markers
uv run pytest -m unit
uv run pytest -m "not slow"
```

### Writing Tests

Example test structure:

```python
"""Tests for module_name."""

import pytest
from llm_discovery.models import Model


class TestModel:
    """Tests for Model class."""

    def test_valid_model_creation(self):
        """Test creating a valid model."""
        model = Model(
            model_id="gpt-4",
            model_name="GPT-4",
            provider_name="openai",
            source=ModelSource.API,
            fetched_at=datetime.now(UTC),
        )
        assert model.model_id == "gpt-4"
```

## Submitting Changes

### Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or changes
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

Example:
```
feat(exporters): add XML export format

- Implement XMLExporter class
- Add tests for XML export
- Update documentation

Closes #123
```

### Pull Request Process

1. **Update your branch** with the latest main:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub with:
   - Clear title and description
   - Reference to related issues
   - Summary of changes
   - Test results

4. **Wait for review** - maintainers will review your PR

5. **Address feedback** - make requested changes and push updates

6. **Merge** - once approved, your PR will be merged

### Pull Request Checklist

- [ ] Tests pass locally (`pytest`)
- [ ] Linting passes (`ruff check`)
- [ ] Type checking passes (`mypy`)
- [ ] Coverage is maintained (90%+)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages follow conventional commits
- [ ] Branch is up to date with main

## Questions?

If you have questions, please:

1. Check existing issues and discussions
2. Review the documentation
3. Open a new issue with your question

Thank you for contributing to llm-discovery!
