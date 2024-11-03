#!/bin/bash
set -e

psql <<- EOSQL
    CREATE USER $POSTGRES_USER;
    CREATE DATABASE $POSTGRES_DB;
    \c $POSTGRES_DB
    CREATE EXTENSION vector;
    CREATE TABLE $GSCHOLAR_TABLE (
        title TEXT,
        link VARCHAR(2048) PRIMARY KEY,
        citation_count INT,
        authors TEXT,
        content TEXT,
        embedding vector(1536)
    );
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
EOSQL
