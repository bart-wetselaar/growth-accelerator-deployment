#!/bin/bash

# Azure Web App startup script for Growth Accelerator Platform
echo "Starting Growth Accelerator Platform..."

# Set Python path
export PYTHONPATH="/home/site/wwwroot:$PYTHONPATH"

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 main:app
