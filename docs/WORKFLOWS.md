# GitHub Actions Workflows

This document explains the GitHub Actions workflows used in the calibration-service project.

## Overview

The project uses GitHub Actions for continuous integration and testing. The workflows are designed to validate code
changes, run tests, and ensure the application behaves as expected.

All workflows use [uv](https://github.com/astral-sh/uv) for Python dependency management and virtual environment
creation, providing fast and reliable dependency resolution.

## Workflows

### 1. CI Workflow (`ci.yaml`)

This is the main CI workflow that runs on pushes to main, pull requests, and manual triggers.

**Jobs:**

- **python-tests**: Runs Python unit and integration tests with coverage
- **build**: Builds the Docker image and uploads it as an artifact
- **container-tests**: Tests the Docker image functionality

**Features:**

- Complete end-to-end testing (in future)
- Docker image validation
- Test report generation
- Code coverage analysis

### 2. Python Tests Workflow (`pytest.yaml`)

This workflow focuses specifically on Python testing and runs when Python files or related configurations change.

**Jobs:**

- **test**: Runs Python unit and integration tests with coverage

**Features:**

- Faster feedback for Python code changes
- Test report generation
- Code coverage analysis
- Path-specific triggering to avoid unnecessary runs

### 3. Pyright Workflow (`pyright.yaml`)

This workflow performs static type checking with [Pyright](https://microsoft.github.io/pyright) to ensure type safety
and catch issues early in development.

Configuration is managed in [pyproject.toml](../pyproject.toml).

**Jobs:**

- **typecheck**: Sets up Python environment with uv, then runs Pyright to check types across the codebase

**Features:**

- Fast dependency resolution using uv
- Enforces type-safety/correctness and detects mismatches
- Catches potential runtime issues during development

### 4. Ruff Workflow (`ruff.yaml`)

This workflow uses the [ruff linter](https://docs.astral.sh/ruff/linter/)
and [ruff formatter](https://docs.astral.sh/ruff/formatter/)
to automatically enforce code quality standards.

Ruff is configured via [pyproject.toml](../pyproject.toml) and runs as a CI job to maintain a clean, consistent
codebase.

**Jobs:**

- **ruff**: Runs static analysis to enforce formatting, code style, and detect common issues

**Features:**

- Enforces consistent formatting and PEP 8-style conventions
- Detects unused code, logic errors, and security concerns
- Helps catch issues early, before code is merged

## Test Reports

Both the CI Workflow and the Python Tests Workflow generate and upload test reports as artifacts, which can be
downloaded from the workflow run page.

## Running Tests Locally

Before submitting a pull request, it's recommended to run the tests locally, or rely on the pre-commit git hook.

_For detailed information on how to run tests on localhost, see [./TESTS.md](TESTS.md)._

## CI/CD Pipeline Flow

1. Code is pushed to GitHub
2. GitHub Actions workflows are triggered:
    - Ruff for linting and formatting
    - Pyright for type checking
    - Python Tests for unit and integration testing
    - CI for complete validation including Docker builds
3. Tests are run and reports are generated
4. If all tests pass, the workflow succeeds
5. Test reports and coverage information are available for review

### 5. Fly.io Workflow (`deploy_release.yaml`)

Deploys container to [https://calibration-service.fly.dev](https://calibration-service.fly.dev)

## Future Enhancements

Planned enhancements to the CI/CD pipeline include:

- Integration with deployment workflows
- Performance testing
- Security scanning
- End-to-end testing with ephemeral containers and/or external services
