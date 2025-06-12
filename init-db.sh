#!/bin/bash
set -e

# Function to create users and databases
setup_db() {
  local database=$1
  echo "Creating database '$database' if it does not exist..."
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname=postgres <<-EOSQL
    SELECT 'CREATE DATABASE $database'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$database')
    \gexec
    GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

# Create each database listed in POSTGRES_MULTIPLE_DATABASES
if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
  echo "Multiple databases creation requested: $POSTGRES_MULTIPLE_DATABASES"
  for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
    setup_db $db
  done
  echo "Multiple databases created."
fi
