import numpy as np
import joblib
from tensorflow.keras.models import load_model

# 1. Define Paths (Where your saved files are)
MODEL_PATH = r"D:\realestate\src\models\inference\house_price_model.h5"
SCALER_X_PATH = r"D:\realestate\src\models\inference\scaler_x.pkl"
SCALER_Y_PATH = r"D:\realestate\src\models\inference\scaler_y.pkl"

print("1. Loading the Brain and Tools...")
try:
    # Load the trained model
    model = load_model(MODEL_PATH)
    
    # Load the translators (Scalers)
    scaler_x = joblib.load(SCALER_X_PATH)
    scaler_y = joblib.load(SCALER_Y_PATH)
    print("   -> Success! Files loaded.")
except Exception as e:
    print(f"   -> ERROR: Could not open files. {e}")
    exit()

# 2. Create a "Fake House" to test
# We need 18 features (Bedrooms, Bathrooms, Sqft, etc...)
# Let's pretend: 3 bed, 2 bath, 2000 sqft, etc.
# (We use random numbers for the rest just to test)
print("2. Inventing a house...")
fake_house = np.array([[3, 2.5, 2000, 5000, 2, 0, 0, 3, 8, 2000, 0, 1995, 0, 98001, 47.5, -122.2, 2000, 5000]])

# 3. Translate the house for the model (Scaling)
fake_house_scaled = scaler_x.transform(fake_house)

# 4. Ask the model for a price
print("3. Asking the model for a price...")
prediction_scaled = model.predict(fake_house_scaled)

# 5. Translate the price back to Dollars
predicted_price = scaler_y.inverse_transform(prediction_scaled)

print("\n" + "="*30)
print(f" PREDICTED PRICE: ${predicted_price[0][0]:,.2f}")
print("="*30 + "\n")