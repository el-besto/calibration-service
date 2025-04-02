"""Script runner for bash commands."""

import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import IO

from dotenv import load_dotenv


def ensure_pythonpath() -> dict[str, str]:
    """Ensure PYTHONPATH is set in the environment.

    Returns:
        dict[str, str]: A copy of the environment with PYTHONPATH set
    """
    env = os.environ.copy()
    if "PYTHONPATH" not in env:
        env["PYTHONPATH"] = "./src"
    return env


commands = {
    "dev": "uv run fastapi dev src/drivers/rest/main.py",
    "test": "./scripts/run_tests.sh",
    "test_cov": "./scripts/run_tests_with_coverage.sh",
    "pytest_base": "pytest",
    "lint": "uv tool run ruff check src",
    "typecheck": "uv tool run pyright src",
    "format": "uv tool run ruff format src",
    "precommit": "uv tool run pre-commit",
    "docs_build": "uv tool run mkdocs build",
    "docs_serve": "uv tool run mkdocs serve",
    "docs_deploy": "uv tool run mkdocs gh-deploy",
}


# Environment setup
def _load_env() -> None:
    """Load environment variables from .env files in order of precedence.

    The order of precedence (later files override earlier ones):
    1. .env - Base defaults (in git)
    2. .env.local - Local overrides (git-ignored)
    3. .env.{ENV} - Environment specific (in git)
    4. .env.{ENV}.local - Environment specific local overrides (git-ignored)

    ENV is determined by PYTHON_ENV environment variable (defaults to 'development')
    """
    root_dir = Path(__file__).parent.parent
    env_name = os.getenv("PYTHON_ENV", "development")

    # Define the .env files in order of precedence (first to last)
    env_files = [
        root_dir / ".env",  # Base defaults
        root_dir / ".env.local",  # Local overrides
        root_dir / f".env.{env_name}",  # Environment specific
        root_dir / f".env.{env_name}.local",  # Environment specific local overrides
    ]

    # Load each file if it exists
    for env_file in env_files:
        if env_file.exists():
            print(f"Loading environment from {env_file.name}...")
            load_dotenv(env_file, override=True)  # Later files override earlier ones
        else:
            print(f"No {env_file.name} file found, skipping...")


def _run_command(command: str, *args: str, wait: bool = True) -> None:
    """Run a command with environment variables.

    Args:
        command: The command to run
        *args: Additional arguments to pass to the command
        wait: Whether to wait for the command to complete. Defaults to True.
              Set to False for long-running commands like the dev server.
    """
    # Load environment variables before running any command
    _load_env()

    # Split the command into a list of arguments
    cmd = command.split() + list(args)

    if wait:
        # For short-lived commands, use run with output passthrough
        subprocess.run(cmd, env=ensure_pythonpath(), check=True)
    else:
        # For long-running commands, use Popen with output passthrough
        process = subprocess.Popen(
            cmd,
            env=ensure_pythonpath(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
        )

        # Function to read and print output in real-time
        def print_output(pipe: IO[str], prefix: str = "") -> None:
            for line in pipe:
                # Only prefix with ERROR: if it's actually an error
                if prefix == "ERROR: " and not any(
                    line.startswith(level)
                    for level in ["ERROR:", "WARNING:", "INFO:", "DEBUG:"]
                ):
                    print(f"{prefix}{line}", end="", flush=True)
                else:
                    print(line, end="", flush=True)

        def signal_handler(signum: int, frame: object) -> None:
            """Handle Ctrl+C gracefully."""
            print("\nShutting down...")
            process.send_signal(signal.SIGINT)  # Send SIGINT to the child process
            process.wait()
            sys.exit(0)

        try:
            # Set up signal handler for Ctrl+C
            signal.signal(signal.SIGINT, signal_handler)

            # Start output readers
            import threading

            stdout_thread = threading.Thread(
                target=print_output, args=(process.stdout,)
            )
            stderr_thread = threading.Thread(
                target=print_output, args=(process.stderr, "ERROR: ")
            )
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            # Wait for the process
            process.wait()
        except KeyboardInterrupt:
            print("\nShutting down...")
            process.send_signal(signal.SIGINT)  # Send SIGINT to the child process
            process.wait()
            sys.exit(0)


def _run_script(script_name: str, *args: str) -> None:
    """Run a bash script from the scripts directory with environment variables."""
    # Load environment variables before running any script
    _load_env()

    scripts_dir = Path(__file__).parent
    script_path = scripts_dir / script_name

    subprocess.run([str(script_path), *args], env=ensure_pythonpath(), check=True)


# Development workflow commands
def run_dev() -> None:
    """Run the development server."""
    _run_command(commands["dev"], *sys.argv[1:], wait=False)


def run_format() -> None:
    """Run code formatters."""
    _run_command(commands["format"], *sys.argv[1:])


def run_lint() -> None:
    """Run linters."""
    _run_command(commands["lint"])


def run_typecheck() -> None:
    """Run type checking."""
    _run_command(commands["typecheck"], *sys.argv[1:])


def run_precommit() -> None:
    """Run pre-commit hooks."""
    _run_command(commands["precommit"], *sys.argv[1:])


def run_test() -> None:
    """Run tests using the run_tests.sh script."""
    _run_script("run_tests.sh", "test")


def run_test_cov() -> None:
    """Run tests with coverage using the run_tests.sh script."""
    _run_script("run_tests.sh", "test-cov")


def run_test_debug() -> None:
    """Run tests directly with pytest, enabling debug logging and output."""
    extra_args = sys.argv[2:]
    _run_command(commands["pytest_base"], "-s", "--log-debug", "--no-cov", *extra_args)


def run_check() -> None:
    """Run all checks (pre-commit hooks and tests)."""
    print("Running all checks...")

    print("Running pre-commit hooks...")
    run_precommit()

    print("Running tests...")
    run_test()

    print("All checks completed successfully!")


# Database management commands
def run_db_init() -> None:
    """Initialize the database."""
    _run_script("run_db.sh", "init")


def run_db_migrate() -> None:
    """Run pending database migrations."""
    _run_script("run_db.sh", "migrate")


def run_db_create_migration():
    """Create a new database migration file."""
    message = input("Enter migration message: ")
    _run_command(f'alembic revision --autogenerate -m "{message}"')


def run_seed():
    """Run the database seeding script."""
    _run_command("python scripts/seed_database.py")


# Setup commands
def run_setup() -> None:
    """Run full setup (initialize DB and run tests)."""
    run_db_init()  # Initialize database first
    run_test()  # Then run tests


# Utility commands
def copy_iso() -> None:
    """Copy ISO timestamp to clipboard."""
    _run_script("copy_iso.sh")


def copy_ulid() -> None:
    """Copy ULID to clipboard."""
    _run_script("copy_ulid.sh")


def copy_uuid() -> None:
    """Copy UUID to clipboard."""
    _run_script("copy_uuid.sh")


# documentation
def docs_build() -> None:
    """Build docs"""
    _run_command(commands["docs_build"])


def docs_serve() -> None:
    """Serve docs."""
    _run_command(commands["docs_serve"])


def docs_deploy() -> None:
    """Deploy docs to hithub pages."""
    _run_command(commands["docs_deploy"])


# Main execution block (if needed)
if __name__ == "__main__":
    if len(sys.argv) < 2:  # noqa: PLR2004
        print("Usage: python scripts/bash_runner.py <command> [args...]")
        sys.exit(1)

    command_name = sys.argv[1]
    args = sys.argv[2:]

    func_name = f"run_{command_name}"
    if func_name in globals() and callable(globals()[func_name]):
        # Handle functions that might need specific args like db-create-migration
        if func_name == "run_db_create_migration":
            globals()[func_name]()  # Call simple function
        else:
            globals()[func_name]()  # Call simple functions
    else:
        print(f"Error: Unknown command '{command_name}'")
        sys.exit(1)
