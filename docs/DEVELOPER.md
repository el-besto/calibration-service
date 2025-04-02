# Developer Guide

This guide covers day-to-day development workflows and commands. For initial setup instructions, see
the [README.md](https://github.com/el-besto/calibration-service/blob/main/README.md).

## Environment Configuration

The project uses layered environment files for configuration:

1. `.env` - Base defaults (in git)
2. `.env.local` - Local overrides (git-ignored)
3. `.env.{ENV}` - Environment specific (in git)
4. `.env.{ENV}.local` - Environment specific local overrides (git-ignored)

Environment files are loaded in the order above, with later files overriding earlier ones. The `{ENV}` placeholder is
replaced with the value of `PYTHON_ENV` (defaults to "development").

Example: To run in test environment:

```bash
PYTHON_ENV=test uv run db_init  # Will use .env → .env.local → .env.test → .env.test.local
```

## Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality. These are configured in `.pre-commit-config.yaml`.

### Installed Hooks

| Hook                      | Description                                                                  | When it Runs      |
|---------------------------|------------------------------------------------------------------------------|-------------------|
| `conventional-pre-commit` | Enforces [Conventional Commits](https://www.conventionalcommits.org/) format | On commit message |
| `run_tests`               | Runs project tests                                                           | Before commit     |
| `trailing-whitespace`     | Removes trailing whitespace                                                  | Before commit     |
| `end-of-file-fixer`       | Ensures files end with newline                                               | Before commit     |
| `check-toml`              | Validates TOML files                                                         | Before commit     |
| `check-yaml`              | Validates YAML files                                                         | Before commit     |
| `check-added-large-files` | Prevents large file commits                                                  | Before commit     |
| `ruff`                    | Lints Python code                                                            | Before commit     |
| `ruff-format`             | Formats Python code                                                          | Before commit     |
| `pyright`                 | Type checks Python code                                                      | Before commit     |
| `uv-lock`                 | Updates dependency lock file                                                 | Before commit     |

### Using Pre-commit

```bash
# Install the hooks
pre-commit install --install-hooks

# Run all hooks manually. Note: errors in alembic directory should be ignored.
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

### Commit Message Format

We use conventional commits with the following types:

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `style`: Changes that do not affect the meaning of the code
- `chore`: Other changes that don't modify src or test files
- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to CI configuration files and scripts
- `docs`: Documentation only changes
- `wip`: Work in progress

Example:

```bash
git commit -m "feat: add user authentication"
```

## Available Commands

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

When modifying code:

```bash
# Format and lint code, check types, run tests
uv run check
```

### 3. Database Changes

When modifying models:

```bash
# Create a new migration
uv run db_create "Description of your changes"

# Apply the migration
uv run db_migrate

# Run tests to ensure everything works
uv run test
```

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

Different test scenarios:

```bash
# Run all tests
uv run test

# Run with coverage
uv run test_cov

# Run in test environment
PYTHON_ENV=test uv run test
```

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
