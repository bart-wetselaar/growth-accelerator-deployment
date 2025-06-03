#!/bin/bash
echo "Starting Growth Accelerator Platform..."
export PYTHONPATH="/home/site/wwwroot:$PYTHONPATH"
exec gunicorn --bind 0.0.0.0:8000 --workers 4 main:app
