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
2. Run Docker compose: pull images, builds, runs migrations, seeds and starts the container
   ```bash
   docker compose up
   ```
3. Go to [localhost:8777/docs](http://localhost:8777/docs) - OpenAPI spec to explore the api
4. (Optional) Open online documentation

Note: for local deployment see [D](docs/DEVELOPER.md#running-on-localhost-without-docker-compose)

## Cleanup

```
docker compose down -vv
```

## Points of Interest

- [OpenApi Specification](http://localhost:8777/docs)
- [Calibration Repository (Postgres)](src/infrastructure/repositories/calibration_repository/postgres_repository.py)
- [Tag Repository (Postgres)](src/infrastructure/repositories/tag_repository/postgres_repository.py)
- [Calibration Routes (FastAPI)](src/drivers/rest/routers/calibration_router.py)
- [Tag Routes (FastAPI)](src/drivers/rest/routers/tag_router.py)
- [Calibration Api integration tests](tests/integration/drivers/rest/test_calibration_api.py)
- [Tagging Api integration tests](tests/integration/drivers/rest/test_tagging_api.py)

# Testing the Prompt
```
docker compose exec web uv run test_api
```


## ERD

<img src="docs/assets/ERD.png" alt="ERD" width="500">


## Inspiration

ve been eager to try Clean Architecture, so I was excited to take this project as a chance to dive in outside of work.
In day-to-day development, we often have to focus narrowly on shipping just enough—so it was refreshing to explore a
more deliberate, scalable structure. I started by defining the use case and interfaces, then adapted a MongoDB
repository based on [shaliamekh][mongo-repo], and later swapped in a PostgreSQL version without touching the core logic.
That flexibility—being able to change out infrastructure without rewriting business rules—really drove home the value of
this approach. Clean Architecture made it easy to innovate at the edges while keeping the core solid. If you’re curious
about the structure, I nerded out a bit more in ARCHITECTURE. [ARCHITECTURE](docs/ARCHITECTURE.md)

[mongo-repo]: https://github.com/shaliamekh/clean-architecture-fastapi/blob/main/src/adapters/repositories/auction_repository/mongodb_repository.py

archived

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
