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

# Run the tests
echo "Running unit tests..."
python -m pytest tests/unit -v --no-cov

echo "Running integration tests..."
python -m pytest tests/integration -v --no-cov

echo "Tests completed."
