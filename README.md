# calibration-service

## Overview

This backend service is designed to manage calibrations of a hardware device. Each calibration includes:

- `calibration_type`
- `value`
- `timestamp`
- `username`

Calibrations can be tagged with arbitrary strings to describe different states of a device. Tags can be added or removed
from calibrations, and the tagging history is preserved.

_[Read full project overview](docs/PROJECT.md)_

---

## Pre-requisites

- **Python** 3.12 or higher, [link][python]
- **uv** for python runtime and dependency management, [link][uv]
- **Node.js** for Pyright pre-commit hook execution, [link][pyright]

---

## Getting started

TODO: (docs): add getting started

---

### Test Documentation

This repository includes a comprehensive test harness following Clean Architecture principles.
The testing infrastructure is designed to be expandable and maintainable.

🧠 _For detailed information about the testing approach, see [docs/TESTS.md](docs/TESTS.md)._

---

### Continuous Integration

This project uses GitHub Actions for continuous integration and code quality checks.
All workflows use [`uv`][uv] for fast dependency resolution.

| Workflow                           | Status Badge                         | Description                                                          |
|------------------------------------|--------------------------------------|----------------------------------------------------------------------|
| **CI** (`ci.yaml`)                 | ![ci-badge]                          | Full pipeline: Docker build, integration tests, and coverage reports |
| **Python Tests** (`pytest.yaml`)   | ![pytest-badge]                      | Unit/integration tests and coverage reports                          |
| **Type Checking** (`pyright.yaml`) | ![pyright-badge] ![pyright-official] | Ensures type safety with Pyright                                     |
| **Lint & Format** (`ruff.yaml`)    | ![ruff-badge]                        | Enforces consistent style and detects common issues using Ruff       |

🧠 _For details, see [.github/WORKFLOWS.md](.github/WORKFLOWS.md)._

<!-- Badge references -->

[ci-badge]: https://github.com/el-besto/calibration-service/actions/workflows/ci.yaml/badge.svg

[pytest-badge]: https://github.com/el-besto/calibration-service/actions/workflows/pytest.yaml/badge.svg

[pyright-badge]: https://github.com/el-besto/calibration-service/actions/workflows/pyright.yaml/badge.svg

[pyright-official]: https://microsoft.github.io/pyright/img/pyright_badge.svg

[ruff-badge]: https://github.com/el-besto/calibration-service/actions/workflows/ruff.yaml/badge.svg

<!-- link helpers below -->

[python]: https://www.python.org/downloads/

[uv]: https://docs.astral.sh/uv/

[pyright]: https://microsoft.github.io/pyright/#/installation
