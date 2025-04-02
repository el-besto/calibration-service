# calibration-service

## Pre-requisites

- **Python** 3.12 or higher
- **PostgreSQL** or **SQLite** for database management
- **Docker Desktop** or Docker Compose capable tool (e.g. [podman desktop][podman] or [rancher desktop][rancher])

## Quick Start

### A) Online Deployment

- [Live Site][live-site] - deployed application
- [Live Docs][live-docs] - GitHub pages hosted site

### (B) Offline Deployment Options

#### Prepare

**Download source_:**

- Clone the repository, and go into the project directory `calibration-service`

**Avoid port conflicts:**

- `5777` - port of dev db
- `5778` - port of test db
- `8777` - port of FastAPI web driver

_Troubleshooting: Verify if a local service is listening by run `lsof -i :<port>` to see binding. If
found, `pkill -9 <PID>` to stop_

#### Containerized Deployment

1. Start Docker Desktop
2. Pull images, build, and start container
   ```bash
   docker compose up
   ```
3. Go to [localhost:8777/docs](http://localhost:8777/docs) - OpenAPI spec
4. (Optional) Open online documentation

### C) Local

**Install python runtime and package manager [uv](https://docs.astral.sh/uv/getting-started/installation/#homebrew)**

   ```
   brew install uv
   ```

**Verify executable is found in `$PATH`**

   ```bash
   which uv
   ```

_Troubleshooting: open a new terminal if a directory is not sent to stdout_

**Start db container, initialize database, and run migrations**

   ```bash
   uv run setup
   ```

**(optional) Seed db:**

   ```bash
   uv run db_seed
   ```

_Troubleshooting: run alembic directly using uv_

   ```bash
   PYTHONPATH=${PYTHONPATH:-./src} uv run alembic upgrade head
   ```

**Start the development server:**

   ```bash
   uv run fastapi dev src/drivers/rest/main.py
   ```

## Cleanup

```
docker compose down -vv
```

## ERD
![ERD](docs/assets/ERD.md)


## Additional Documentation

- [Developer Guide](docs/DEVELOPER.md) - Day-to-day development workflows
- [Database Management](docs/DATABASE.md) - Detailed information about database management operations
- [Architecture Inspiration](docs/ARCHITECTURE.md) - System design and software architecture inspiration
- [Testing Approach](docs/TESTS.md) - How to execute project tests and the packages used
- [CI/CD](docs/WORKFLOWS.md) - Description of CI/CD workflows

## License

[License details here]


<!-- link helpers below -->

[podman]: https://podman-desktop.io/

[rancher]: https://rancherdesktop.io/

[live-docs]: https://el-besto.github.io/calibration-service/welcome

[live-site]: https://calibration-service.fly.dev/docs
