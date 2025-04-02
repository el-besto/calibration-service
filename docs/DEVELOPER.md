# Developer Guide

This guide covers day-to-day development workflows and commands. For initial setup instructions, see
the [README.md](https://github.com/el-besto/calibration-service/blob/main/README.md).

## Environment Configuration

The project uses layered environment files for configuration:

1. `.env` - Base defaults (in git)
2. `.env.local` - Local overrides (git-ignored)
3. `.env.{ENV}` - Environment specific (in git)

Environment files are loaded in the order above, with later files overriding earlier ones. The `{ENV}` placeholder is
replaced with the value of `PYTHON_ENV` (defaults to "development").

Example: To run in test environment:

```bash
PYTHON_ENV=test uv run db_init  # Will use .env → .env.local → .env.test → .env.test.local
```

## Available Project Commands

All commands are run using `uv run <command>`. Here's a complete list:

| Command      | Description                                  | Common Use                   |
|--------------|----------------------------------------------|------------------------------|
| `dev`        | Start the development server                 | Local development            |
| `check`      | Runs all "before committing" cmds            | Local development            |
| `format`     | Run code formatters                          | Before committing            |
| `lint`       | Run linters                                  | Before committing            |
| `test`       | Run unit and integration tests               | Before committing            |
| `test_debug` | Run `test` and prints `log_test_step` output | Debugging failed tests       |
| `test_cov`   | Run tests with coverage report               | CI/CD, coverage checks       |
| `typecheck`  | Run type checker                             | Before committing            |
| `db_init`    | Initialize database and run migrations       | First-time setup, reset DB   |
| `db_migrate` | Apply pending migrations                     | After pulling new migrations |
| `db_create`  | Create a new migration                       | After model changes          |
| `setup`      | Full setup (init DB and run tests)           | First-time setup, CI/CD      |
| `cp_iso`     | Copy ISO timestamp to clipboard              | Creating timestamps          |
| `cp_ulid`    | Copy ULID to clipboard                       | Creating unique IDs          |
| `cp_uuid`    | Copy UUID to clipboard                       | Creating unique IDs          |

__see: `pyproject.toml`'s `[project.scripts]` for details. All are proxied through the `scripts/bash_runner.py` module.

## Common Development Workflows

### 1. Daily Development

Start your day with:

```bash
# Pull latest changes
git pull

# Apply any new migrations
uv run db_migrate

# Start the development server
uv run dev
```

### 2. Making Changes

When modifying code periodically run:

```bash
# Format and lint code, check types, run tests
uv run check
```

### 3. Database Changes

_[see DATABASE.md](DATABASE.md)_


### 4. Pre-commit Checklist

The pre-commit hooks will run automatically, but you can also run them manually:

```bash
# Run all pre-commit hooks
uv run pre-commit run --all-files

# If all pass, commit your changes
git add .
git commit -m "feat: your feature description"
```

### 5. Running Tests

[see TESTS.md](TESTS.md#running-tests)

## Best Practices

1. **Environment Variables**
    - Never commit sensitive values to git
    - Use `.env.local` for local development overrides
    - Use environment-specific files for different configurations

2. **Database Migrations**
    - One migration per model change
    - Write meaningful migration messages
    - Always run tests after applying migrations

3. **Code Quality**
    - Let pre-commit hooks run automatically
    - Fix issues before committing
    - Keep test coverage high

4. **Testing**
    - Write tests before fixing bugs
    - Update tests when changing features
    - Use appropriate test environment

## Troubleshooting

Common issues and solutions:

1. **Database Connection Issues**
   ```bash
   # Reset database and migrations
   uv run db_init
   ```

2. **Environment Issues**
   ```bash
   # Verify environment
   cat .env
   cat .env.local  # If it exists
   ```

3. **Pre-commit Hook Issues**
   ```bash
   # Update hooks to latest version
   pre-commit clean
   pre-commit install --install-hooks
   ```

4. **Test Database Issues**
   ```bash
   # Run with test environment
   PYTHON_ENV=test uv run db_init
   PYTHON_ENV=test uv run test
   ```

For more detailed information about the architecture and design decisions, see [ARCHITECTURE.md](./ARCHITECTURE.md).
