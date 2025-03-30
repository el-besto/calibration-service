#!/bin/bash

# Function to load environment variables
load_env() {
    if [ -f ".env" ]; then
        echo "Loading environment from .env file..."
        set -o allexport
        source .env
        set +o allexport
    else
        echo "No .env file found, using existing environment variables..."
    fi
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    PYTHONPATH=${PYTHONPATH:-./src} uv run alembic upgrade head
}

# Function to initialize database
init_database() {
    echo "Initializing database..."
    # Start PostgreSQL container if not running and we're in local development
    if [ -z "$CI" ] && ! docker compose ps | grep -q "postgres.*running"; then
        echo "Starting PostgreSQL container..."
        docker compose up -d postgres
        # Wait for PostgreSQL to be ready
        echo "Waiting for PostgreSQL to be ready..."
        sleep 5
    fi
    # Run migrations
    run_migrations
}

# Function to create a new migration
create_migration() {
    local message=$1
    if [ -z "$message" ]; then
        echo "Error: Migration message is required"
        echo "Usage: $0 create 'migration message'"
        exit 1
    fi
    echo "Creating new migration: $message"
    PYTHONPATH=${PYTHONPATH:-./src} uv run alembic revision --autogenerate -m "$message"
}

# Load environment variables
load_env

# Parse command line arguments
case "$1" in
    "init")
        init_database
        ;;
    "migrate")
        run_migrations
        ;;
    "create")
        create_migration "$2"
        ;;
    *)
        echo "Usage: $0 {init|migrate|create 'migration message'}"
        exit 1
        ;;
esac

echo "Database operation completed."
