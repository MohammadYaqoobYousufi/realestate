# Local-only setup (Ollama + PostgreSQL)

Goal: run the full stack on a single laptop with no paid services or external APIs. Use Ollama as the local LLM host and PostgreSQL (with pgvector) as the primary analytical DB.

Summary (minimal, offline):
- Install Ollama locally (WSL2 recommended on Windows if native installer isn't available).
- Run a suitable local model in Ollama (GGML/LLM model) that supports completion and embeddings.
- Install PostgreSQL locally and enable `pgvector` extension (or use a Docker container).
- Use Python environment (`envs` venv in this repo) to run everything via local dependencies (psycopg, sqlalchemy, pgvector, faiss-cpu or sentence-transformers for embeddings if needed).

Why this configuration?
- No external paid APIs required: LLMs run locally via Ollama; storage and computing are on your laptop.
- PostgreSQL + pgvector provides a durable, local vector-capable database and is compatible with the project's technical requirements.

Prerequisites
- A laptop with sufficient disk (model files can be tens of GB) and memory (ideally 16+ GB). Smaller models will run on lower-end machines.
- Windows with WSL2 (recommended) or native Linux/macOS.
- Docker is optional but recommended for Postgres and pgvector if you prefer containerized setup.

Quick install steps (high level)
1. Install Ollama
   - On Windows, use WSL2 or follow Ollama's Windows instructions if available. Ensure Ollama is running and reachable on localhost.
2. Install PostgreSQL
   - Option A: Docker: `docker run --name realestate-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15`
   - Option B: native installer from postgresql.org
   - Once running, connect and run: `CREATE EXTENSION IF NOT EXISTS vector;` to add `pgvector` support.
3. Configure repo
   - Activate venv: `envs\Scripts\Activate.ps1`
   - Install Python deps: `pip install -r requirements.txt`
   - Set environment variables in a local `.env` (example below)

Example `.env` (local-only):
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/realestate
OLLAMA_URL=http://localhost:11434
USE_LOCAL_MODELS=1
```

Local embedding models
- If your Ollama model supports embeddings via API, use it. Otherwise, use `sentence-transformers` or `open-source embedding models` that can run locally.

Safety & licensing
- Model licensing matters. Ensure any model you download and run locally allows your intended use (commercial vs research licenses).

Next steps in this repo
- Use `scripts/check_local_stack.py` to verify Ollama and Postgres are reachable and properly configured.
- Use `demos/ollama_client.py` as a starting point for local LLM calls.

If you want, I can add a `docker-compose.yml` that brings up Postgres with `pgvector` and optionally a small local HTTP proxy for Ollama.
