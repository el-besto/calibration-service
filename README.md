# calibration-service

## Overview

This backend service is designed to manage calibrations of a hardware device. Each calibration includes:

- `calibration_type`
- `value`
- `timestamp`
- `username`

Calibrations can be tagged with arbitrary strings to describe different states of a device. Tags can be added or removed
from calibrations, and the tagging history is preserved.

_[Read full project overview](docs/PROJECT.md)

[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)
[![Python Tests](https://github.com/el-besto/calibration-service/actions/workflows/pytest.yaml/badge.svg)](https://github.com/el-besto/calibration-service/actions/workflows/pytest.yaml)

---

## Pre-requisites

- **Python** 3.12 or higher, [link][python]
- **uv** for python runtime and dependency management, [link][uv]
- **nodejs** for Pyright pre-commit hook execution, [link][pyright]

---

## Getting started

TODO: (docs): add getting started

---

### Test Documentation

This repository includes a comprehensive test harness following Clean Architecture principles.
The testing infrastructure is designed to be expandable and maintainable.

_For detailed information about the testing approach, see [docs/TESTS.md](docs/TESTS.md)._

---

## Additional Documentation

- [Full Project Overview](docs/PROJECT.md)

---

<!-- link helpers below -->

[python]: https://www.python.org/downloads/

[uv]: https://docs.astral.sh/uv/

[pyright]: https://microsoft.github.io/pyright/#/installation
