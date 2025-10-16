#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# Start the FastAPI application using Uvicorn
# The --host 0.0.0.0 is crucial for Render to bind to the correct network interface.
# The $PORT variable is automatically set by Render.
echo "Starting Uvicorn server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT