# Database Overview

## Technology

- **PostgreSQL 16** with the **pgvector** extension for relational data and vector embeddings.
- **Async SQLAlchemy 2.0** as the ORM, providing asynchronous database access throughout the application.
- **Alembic** for schema migrations.

## Key Tables

| Table | Description |
|-------|-------------|
| `users` | User accounts and profiles |
| `documents` | Uploaded document metadata and status |
| `document_chunks` | Text chunks with their vector embeddings for semantic search |
| `conversations` | Chat conversation sessions |
| `messages` | Individual messages within conversations |
| `analysis_results` | Document analysis output and metrics |

## Migrations

Migrations are managed with Alembic and live in `apps/backend/alembic/`.

```bash
# Enter the backend directory
cd apps/backend

# Auto-generate a migration from model changes
alembic revision --autogenerate -m "description of changes"

# Apply pending migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

## Key Design Decisions

- **UUID primary keys** for all tables — avoids enumeration attacks and simplifies distributed ID generation.
- **Soft deletes** for user-facing resources (documents, conversations) to allow recovery.
- **Created/updated timestamps** on every table for auditing and debugging.
- **Vector index** on `document_chunks.embedding` using HNSW (Hierarchical Navigable Small World) for fast similarity search.
