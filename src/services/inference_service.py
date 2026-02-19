import numpy as np
from app.services.model_registry_service import load_latest_model
from app.services.feature_service import get_features_for_roll

model, model_id = load_latest_model()

def predict_value(roll_number: int):

    features = get_features_for_roll(roll_number)

    pred_log = model.predict(features)[0]
    pred_value = float(np.exp(pred_log) - 1)

    return {
        "prediction": pred_value,
        "model_id": model_id,
        "features": features
    }