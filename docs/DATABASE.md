# Database Management

This document covers database management, migrations, and best practices for this project.

## Overview

The project uses:

- PostgreSQL as the database
- SQLAlchemy for ORM and database operations
- Alembic for database migrations
- Automatic migration generation from SQLAlchemy models

## Directory Structure

```
src/
├── infrastructure/
│   └── orm_models.py    # SQLAlchemy models
├── config/
│   └── database.py      # Database configuration
└── alembic/
    ├── versions/        # Migration version files
    ├── env.py          # Migration environment configuration
    └── script.py.mako  # Migration script template
```

## Common Operations

The project provides several commands for database management:

## Database Management

The service uses PostgreSQL for data storage and Alembic for database migrations. Key commands:

```bash
# Initialize database and run migrations
uv run db_init

# Apply pending migrations
uv run db_migrate

# Create a new migration
uv run db_create "Description of changes"

# Seed data
uv run db_seed
```

## Migration Management

### Creating Migrations

When you modify SQLAlchemy models in `orm_models/`, create a new migration:

```bash
uv run db_create "Add status column to Calibration model"
```

Always:

1. Review the generated migration in `alembic/versions/`
2. Check indexes and constraints
3. Add any necessary data migrations
4. Run tests before committing

### Applying Migrations

To apply pending migrations:

```bash
# Development environment
uv run db_migrate

# Test environment
PYTHON_ENV=test uv run db_migrate
```

### Advanced Operations

For advanced cases, you can use direct Alembic commands:

```bash
# Roll back one migration
PYTHONPATH=./src uv run alembic downgrade -1

# View migration history
PYTHONPATH=./src uv run alembic history --verbose

# Roll back to specific version
PYTHONPATH=./src uv run alembic downgrade <version_id>
```

## Best Practices

### 1. Migration Management

- One migration per model change
- Write descriptive migration messages
- Include model name in migration message
- Review generated migrations before committing
- Test both upgrade and downgrade paths

### 2. Data Safety

- Always backup production data before migrations
- Test migrations on development first
- Include data migrations when needed
- Verify data integrity after migration

### 3. Development Workflow

- Create migrations in feature branches
- Run full test suite after migrations
- Document significant migrations
- Use appropriate environment for testing

### 4. Error Handling

- Never edit committed migrations
- Create new migrations for fixes
- Roll back failed migrations cleanly
- Check database state before retrying

## Environment Configuration

The database system uses the project's layered environment configuration:

1. `.env` - Base defaults (in git)
2. `.env.local` - Local overrides (git-ignored)
3. `.env.{ENV}` - Environment specific (in git)
4. `.env.{ENV}.local` - Environment specific local overrides (git-ignored)

Example configurations:

```bash
# .env (base defaults)
DATABASE_URL=postgresql+asyncpg://dev-user:password@localhost:5777/dev_db

# .env.test
DATABASE_URL=postgresql+asyncpg://test-user:password@localhost:5778/test_db
```

## Troubleshooting

### 1. Migration Not Detected

- Ensure model is imported in `orm_models/__init__.py`
- Verify model inherits from `Base`
- Check for circular imports
- Run with `--verbose` flag for more details

### 2. Connection Issues

```bash
# Verify database is running
docker compose ps

# Check connection
uv run db_init

# Reset database (development only)
docker compose down -v postgres
uv run db_init
```

### 3. Migration Conflicts

- Never edit committed migrations
- Create new migrations for fixes
- Use `alembic history` to check state
- Consider rolling back if needed

### 4. Environment Issues

```bash
# Check current settings
cat .env
cat .env.local  # If it exists

# Verify environment
echo $PYTHON_ENV
echo $DATABASE_URL
```

For more information about development workflows, see [DEVELOPER.md](./DEVELOPER.md).
