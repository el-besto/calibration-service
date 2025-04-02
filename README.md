# calibration-service

[Live Site](https://calibration-service.fly.dev/docs)
[Live Documentation](https://el-besto.github.io/calibration-service)

## Quick Start (container)

1. Start Docker Desktop
2. Pull images, build, and start container
   ```bash
   docker compose up
   ```
3. Go to [localhost:8000/docs](http://localhost:8000/docs)

## Quick Start (local)

1. Clone the repository
2. Install python runtime and package manager [uv](https://docs.astral.sh/uv/getting-started/installation/#homebrew)
   ```
   brew install uv
   ```
3. Start containers, initialize database, and run migrations
   ```bash
   uv run db_init"
   ```
4. (optional) Seed db:
   ```bash
   uv run seed
   ```
5. Start the development server:
   ```bash
   uv run fastapi dev src/drivers/rest/main.py
   ```

## Database Management

The service uses PostgreSQL for data storage and Alembic for database migrations. Key commands:

```bash
# Initialize database and run migrations
uv run db_init

# Apply pending migrations
uv run db_migrate

# Create a new migration
uv run db_create "Description of changes"
```

For detailed information about database operations and migrations, see:
- [Developer Guide](docs/DEVELOPER.md) - Day-to-day development workflows
- [Database Migrations](alembic/README.md) - Detailed Alembic usage and best practices

## Documentation

- [Developer Guide](docs/DEVELOPER.md) - Development workflows and commands
- [Architecture](docs/ARCHITECTURE.md) - System design and patterns
- [Database Migrations](alembic/README.md) - Database management details

## License

[License details here]
