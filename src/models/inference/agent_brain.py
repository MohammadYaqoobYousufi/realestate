import joblib
from tensorflow.keras.models import load_model
import numpy as np

class RealEstateAI:
    def __init__(self):
        # Path to the files you just saved
        self.model = load_model(r'D:\realestate\src\models\inference\house_price_model.h5')
        self.scaler_x = joblib.load(r'D:\realestate\src\models\inference\scaler_x.pkl')
        self.scaler_y = joblib.load(r'D:\realestate\src\models\inference\scaler_y.pkl')

    def predict(self, features):
        # 1. Scale the input
        features_scaled = self.scaler_x.transform([features])
        # 2. Predict
        prediction_scaled = self.model.predict(features_scaled)
        # 3. Inverse scale to get actual dollars
        final_price = self.scaler_y.inverse_transform(prediction_scaled)
        return final_price[0][0]

# Usage Example:
# ai = RealEstateAI()
# price = ai.predict([3, 2, 1500, ...]) # 18 features