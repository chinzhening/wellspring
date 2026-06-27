-- Enable PostgreSQL extensions required by the application.
-- pg_trgm: trigram-based fuzzy string matching (used for song/media matching).
-- vector: pgvector support for storing and querying embedding vectors.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;