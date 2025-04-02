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