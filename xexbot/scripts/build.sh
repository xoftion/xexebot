#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Initialize the database
echo "Initializing the database..."
python -m app.db
