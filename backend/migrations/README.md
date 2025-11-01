# Database Migrations

This directory contains SQL migrations for the OpenAI Assistant orchestrator database.

## Setup

### 1. Create Database and User

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database and user
CREATE DATABASE opa;
CREATE USER opa WITH PASSWORD 'opa_password';
GRANT ALL PRIVILEGES ON DATABASE opa TO opa;

# Grant schema permissions
\c opa
GRANT ALL ON SCHEMA public TO opa;
```

### 2. Run Migrations

```bash
# Run in order
psql -U opa -d opa -f 001_initial_schema.sql
psql -U opa -d opa -f 002_hybrid_search_functions.sql
```

### 3. Verify Setup

```bash
psql -U opa -d opa

# Check tables
\dt

# Check functions
\df

# Test memory insert
INSERT INTO memory_items (id, text, tags)
VALUES ('test123', 'This is a test memory', ARRAY['test', 'demo']);

# Test hybrid search (requires embedding)
-- See backend/app/tools/embedding.py for generating embeddings
```

## Migration Files

### 001_initial_schema.sql
- Creates `memory_items` table with pgvector support
- Creates `jobs` table for orchestrator tracking
- Sets up indexes (GIN for tags, IVFFlat for vectors, GIN trigram for text)
- Creates enum types for job status and execution mode
- Adds trigger for auto-updating `updated_at`

### 002_hybrid_search_functions.sql
- `bm25_score()`: Calculate BM25 relevance for text search
- `hybrid_search()`: Combine BM25 + vector search with configurable weights
- `vector_search()`: Pure semantic similarity search
- `bm25_search()`: Pure keyword search

## Usage Examples

### Insert Memory with Embedding

```python
from app.models import MemoryItem
from app.core.db import async_session_maker
from app.tools.embedding import generate_embedding

async def store_memory(text: str, tags: list[str]):
    embedding = await generate_embedding(text)
    
    async with async_session_maker() as session:
        memory = MemoryItem(
            id=hashlib.sha256(f"{text}{tags}".encode()).hexdigest(),
            text=text,
            tags=tags,
            embedding=embedding
        )
        session.add(memory)
        await session.commit()
```

### Hybrid Search Query

```sql
-- Search for memories about "python programming"
-- with 50% keyword weight, 50% semantic weight
SELECT * FROM hybrid_search(
    'python programming',
    '[0.1, 0.2, ...]'::vector(384),  -- Query embedding
    ARRAY['coding']::TEXT[],         -- Filter by tags
    10,                              -- Top 10 results
    0.5,                             -- BM25 weight
    0.5                              -- Vector weight
);
```

### Pure Vector Search

```sql
-- Semantic similarity only
SELECT * FROM vector_search(
    '[0.1, 0.2, ...]'::vector(384),
    ARRAY[]::TEXT[],  -- No tag filter
    5                 -- Top 5 results
);
```

## Rollback

To drop all tables and start fresh:

```sql
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS memory_items CASCADE;
DROP TYPE IF EXISTS job_status CASCADE;
DROP TYPE IF EXISTS execution_mode CASCADE;
DROP FUNCTION IF EXISTS bm25_score CASCADE;
DROP FUNCTION IF EXISTS hybrid_search CASCADE;
DROP FUNCTION IF EXISTS vector_search CASCADE;
DROP FUNCTION IF EXISTS bm25_search CASCADE;
DROP EXTENSION IF EXISTS vector CASCADE;
DROP EXTENSION IF EXISTS pg_trgm CASCADE;
```

## Environment Variables

Set these in `.env`:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=opa
POSTGRES_USER=opa
POSTGRES_PASSWORD=opa_password
```

## Docker Compose

If using Docker:

```yaml
postgres:
  image: pgvector/pgvector:pg16
  environment:
    POSTGRES_USER: opa
    POSTGRES_PASSWORD: opa_password
    POSTGRES_DB: opa
  volumes:
    - ./migrations:/docker-entrypoint-initdb.d
  ports:
    - "5432:5432"
```

The migrations will auto-run on first container startup.
