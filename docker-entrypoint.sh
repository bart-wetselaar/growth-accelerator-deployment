#!/bin/bash
# Docker entrypoint script for Growth Accelerator Staffing Platform

set -e

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
  echo "Waiting for PostgreSQL to be ready..."
  
  # Extract values from DATABASE_URL
  if [[ "$DATABASE_URL" =~ postgres://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
    
    if [[ "$DB_NAME" =~ (.+)\?.+ ]]; then
      DB_NAME="${BASH_REMATCH[1]}"
    fi
    
    # Wait for PostgreSQL to be ready
    until PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
      echo "PostgreSQL is unavailable - sleeping"
      sleep 2
    done
    
    echo "PostgreSQL is up - executing command"
  else
    echo "DATABASE_URL is not properly formatted - skipping PostgreSQL check"
  fi
}

# Create health check endpoint
create_health_endpoint() {
  echo "Creating health check endpoint..."
  
  # Create health.py module if it doesn't exist
  if [ ! -f /app/health.py ]; then
    cat > /app/health.py << 'EOF'
from flask import Blueprint, jsonify
import os
import psycopg2
import socket
import time

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    status = {'status': 'healthy', 'checks': {}}
    
    # Check database connection
    try:
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
            status['checks']['database'] = 'ok'
        else:
            status['checks']['database'] = 'not configured'
    except Exception as e:
        status['checks']['database'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Check environment
    status['checks']['environment'] = os.environ.get('FLASK_ENV', 'production')
    
    # Add server info
    status['server'] = {
        'hostname': socket.gethostname(),
        'timestamp': int(time.time())
    }
    
    return jsonify(status)
EOF
    
    # Modify main.py to register the health blueprint
    if [ -f /app/main.py ]; then
      grep -q "health_bp" /app/main.py || sed -i '/from flask import/a import health' /app/main.py
      grep -q "app.register_blueprint(health_bp)" /app/main.py || sed -i '/app = Flask/a app.register_blueprint(health.health_bp)' /app/main.py
    elif [ -f /app/app.py ]; then
      grep -q "health_bp" /app/app.py || sed -i '/from flask import/a import health' /app/app.py
      grep -q "app.register_blueprint(health_bp)" /app/app.py || sed -i '/app = Flask/a app.register_blueprint(health.health_bp)' /app/app.py
    fi
  fi
}

# Apply database migrations if needed
apply_migrations() {
  echo "Applying database migrations if needed..."
  
  # Check if we have Flask-Migrate installed and a migrations directory
  if [ -d /app/migrations ] && python -c "import flask_migrate" &>/dev/null; then
    echo "Running Flask-Migrate database migrations..."
    flask db upgrade
  else
    echo "No Flask-Migrate migrations found - skipping"
  fi
}

# Wait for PostgreSQL if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
  apt-get update && apt-get install -y postgresql-client
  wait_for_postgres
fi

# Create health endpoint
create_health_endpoint

# Apply migrations
apply_migrations

# Execute the command
exec "$@"