"""Smoke test for the realestate Python environment.

Usage: activate venv then run:
    python scripts/check_env.py

This verifies that the model and scalers load and that a one-shot prediction runs.
"""
from pathlib import Path
import joblib
import numpy as np
try:
    from tensorflow.keras.models import load_model
except Exception as e:
    raise SystemExit("TensorFlow not available or failed to import: %s" % e)

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "src" / "models" / "inference" / "house_price_model.h5"
SCX = ROOT / "src" / "models" / "inference" / "scaler_x.pkl"
SCY = ROOT / "src" / "models" / "inference" / "scaler_y.pkl"

print("Model path:", MODEL)
print("Scaler X path:", SCX)
print("Scaler Y path:", SCY)

if not MODEL.exists() or not SCX.exists() or not SCY.exists():
    raise SystemExit("One or more required model files are missing. Check paths in repository.")

print("Loading model (this may take a few seconds)...")
model = load_model(str(MODEL))
print("Model loaded:", type(model))

print("Loading scalers...")
scx = joblib.load(str(SCX))
scy = joblib.load(str(SCY))
print("Scalers loaded:", type(scx), type(scy))

# Sample input matching the app mapping
X = np.array([[3, 2.0, 2000, 5000, 1, 0, 0, 3, 7, 2000, 0, 2000, 0, 98001, 47.5, -122.2, 2000, 5000]])
X_s = scx.transform(X)
print("Input scaled shape:", X_s.shape)

pred = model.predict(X_s)
price = scy.inverse_transform(pred)[0][0]
print(f"Smoke-test prediction OK: ${price:,.2f}")
print("All checks passed.")
