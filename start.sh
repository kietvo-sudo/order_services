#!/bin/bash
# Start script for Order Services API
# Supports PORT environment variable from cloud platforms (Render, Heroku, etc.)

# Get port from environment variable or use default
PORT=${PORT:-8000}

# Start uvicorn server
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT

