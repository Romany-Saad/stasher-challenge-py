#!/bin/bash
set -e

# Create the main test database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE stasher_interview_test;
EOSQL

# Connect to the test database and enable the PostGIS extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "stasher_interview_test" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL