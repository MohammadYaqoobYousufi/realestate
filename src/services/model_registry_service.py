import joblib
from sqlalchemy import text
from app.db.session import engine

def load_latest_model():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT model_id, artifact_path
            FROM feature_store.model_registry
            ORDER BY created_at DESC
            LIMIT 1
        """)).fetchone()

    model = joblib.load(result.artifact_path)
    return model, result.model_id