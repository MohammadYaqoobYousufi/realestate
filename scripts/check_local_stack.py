"""Lightweight checks for local-only stack (Ollama + Postgres + pgvector).

Run: `envs\Scripts\Activate.ps1` then `python scripts/check_local_stack.py`
"""
import os
import socket
import psycopg

def check_port(host, port, timeout=2.0):
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except Exception:
        return False


def check_postgres(dsn):
    try:
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                return True, 'Postgres reachable and pgvector extension ok.'
    except Exception as e:
        return False, str(e)


if __name__ == '__main__':
    print('Checking Ollama (default host=localhost port=11434) ...')
    ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    # parse host/port
    try:
        host = 'localhost'
        port = 11434
        host_port_ok = check_port(host, port)
    except Exception:
        host_port_ok = False

    print('  Ollama listening on port 11434:' , host_port_ok)

    db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
    ok, msg = check_postgres(db_url)
    print('Postgres check:', ok, msg)

    if host_port_ok and ok:
        print('\nLocal stack looks reachable. You can proceed to run local ingestion & models.')
    else:
        print('\nOne or more checks failed. See messages above and follow docs/LOCAL_SETUP_OLLAMA.md')
