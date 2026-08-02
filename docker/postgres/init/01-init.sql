-- ProjectLens AI — PostgreSQL init.
-- The schema itself is owned by Alembic migrations (alembic upgrade head runs
-- before uvicorn starts). This script only enables the pgvector extension the
-- image ships with; legacy `documents` / `document_chunks` tables that nothing
-- used were removed.
CREATE EXTENSION IF NOT EXISTS vector;
