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

# Run all tests with coverage reporting
echo "Running all tests with coverage..."
python -m pytest

echo "Tests completed. Coverage reports generated in:"
echo "- HTML report: coverage_html/index.html"
echo "- XML report: coverage.xml"
