-- Initialization SQL for Postgres container
-- This script will run at first container startup (mounted into /docker-entrypoint-initdb.d)

-- Create pgvector extension in the target DB
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a schema for our application (optional)
CREATE SCHEMA IF NOT EXISTS realestate;

-- Create a minimal test table to verify the vector extension works (optional)
CREATE TABLE IF NOT EXISTS realestate.sample_vectors (
  id serial PRIMARY KEY,
  description text,
  embedding vector(1536)  -- example dimension, change to your model's dim
);
