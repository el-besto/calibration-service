#!/bin/bash

# Set up environment
echo "Setting up test environment..."

# Create or activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install test dependencies if needed
echo "Installing test dependencies..."
uv sync --group dev

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    PYTHONPATH=./src uv run alembic upgrade head
}

# Function to initialize database
init_database() {
    echo "Initializing database..."
    # Start PostgreSQL container if not running
    if ! docker compose ps | grep -q "postgres.*running"; then
        echo "Starting PostgreSQL container..."
        docker compose up -d postgres
        # Wait for PostgreSQL to be ready
        echo "Waiting for PostgreSQL to be ready..."
        sleep 5
    fi
    # Run migrations
    run_migrations
}

# Parse command line arguments
case "$1" in
    "init")
        init_database
        ;;
    "migrate")
        run_migrations
        ;;
    "test")
        # Run the tests
        echo "Running unit tests..."
        python -m pytest tests/unit -v --no-cov

        echo "Running integration tests..."
        python -m pytest tests/integration -v --no-cov
        ;;
    "test_integration")
        echo "Running integration tests..."
        python -m pytest tests/integration -v --no-cov
        ;;
    "test_api")
        echo "Running api component integration tests..."
        python -m pytest tests/integration/drivers -v --no-cov
        ;;
    "test_e2e")
      echo "Running e2e tests to validate the system..."
      python -m pytest tests/integration/drivers -v --no-cov
      ;;
    "setup")
        # Full setup: initialize DB and run tests
        init_database
        echo "Running unit tests..."
        python -m pytest tests/unit -v --no-cov
        echo "Running integration tests..."
        python -m pytest tests/integration -v --no-cov
        ;;
    *)
        echo "Usage: $0 {init|migrate|test|setup}"
        exit 1
        ;;
esac

echo "Operation completed."
