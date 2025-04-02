# Testing Strategy for Calibration Service

This document outlines the testing strategy for the Calibration Service, following Clean Architecture principles.

## Test Structure

The test suite is organized into the following categories:

- **Unit Tests**: Testing individual components in isolation
    - `tests/unit/entities`: Tests for entity models and validation
    - `tests/unit/application`: Tests for use cases and business logic
    - `tests/unit/infrastructure`: Tests for repositories and services
    - `tests/unit/interface_adapters`: Tests for controllers
    - `tests/unit/use_cases`: Tests for use cases

- **Integration Tests**: Testing the interaction between components
    - `tests/integration`: API endpoint testing with in-memory repositories

- **End-to-End Tests**: Testing the entire system (future implementation)
    - `tests/e2e`: Full system tests with external dependencies

## Test Dependencies

The test suite uses the following dependencies:

- **pytest**: The core testing framework
- **httpx**: HTTP client for testing FastAPI endpoints
- **pytest-asyncio**: Support for asynchronous tests
- **pytest-cov**: Code coverage reporting

## Running Tests

Different test scenarios:

```bash
# Run all tests
uv run test

# Run with coverage
uv run test_cov

# Run in test environment
PYTHON_ENV=test uv run test
```

Tests can also be run using the `run_tests.sh` script:

  ```bash
  ./scripts/run_tests.sh
  ```

> [!NOTE]
> run_tests is executed by pre-commit as a pre-commit hook. [More info in](CONTRIBUTING.md#pre-commit-hooks) 

_Generate coverage reports using the `run_tests_with_coverage.sh` script:_

  ```bash
  ./scripts/run_tests_with_coverage.sh
  ```

Or, run manually:

  ```bash
  # Run all tests
  PYTHONPATH=./src python -m pytest -v --no-cov

  # Run unit tests only
  python -m pytest tests/unit -v --no-cov

  # Run integration tests only
  python -m pytest tests/integration -v --no-cov

  # Run with coverage (pytest.ini passes coverage flags by default)
  python -m pytest
  ```

## Test Data

- **Unit Tests**: Use mock objects and in-memory repositories
- **Integration Tests**: Use in-memory repositories for isolation
~~- **E2E Tests**: Will use test databases or containerized services~~ (future)

## Clean Architecture Testing Approach

Our (ideal) testing follows Clean Architecture principles:

1. **Entities Tests**: Verify that our core models work correctly
2. **Use Case Tests**: Ensure business rules are correctly implemented
3. **Interface Adapter Tests**: Validate controllers and presenters
4. **Framework Tests**: Test the FastAPI endpoints

By following this approach, we can ensure that our business logic remains independent of frameworks and external
concerns, making our tests more robust and our code more maintainable.
