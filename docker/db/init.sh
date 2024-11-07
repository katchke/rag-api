#!/bin/bash
set -e

psql <<- EOSQL
    CREATE USER $POSTGRES_USER;
    CREATE DATABASE $POSTGRES_DB;
    \c $POSTGRES_DB
    CREATE EXTENSION vector;
    CREATE TABLE $ARXIV_TABLE (
        title TEXT,
        link VARCHAR(2048),
        chunk_num INT,
        authors TEXT,
        content TEXT,
        embedding vector(1536),
        PRIMARY KEY (link, chunk_num)
    );
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
EOSQL
