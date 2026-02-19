import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score
from tensorflow.keras.models import Sequential 
from tensorflow.keras.layers import Dense, Input
import os

# --- CONFIGURATION ---
DATA_PATH = r"D:\realestate\data\raw\realestate_prices.csv"
MODEL_SAVE_PATH = r"D:\realestate\src\models\inference\house_price_model.h5"
SCALER_X_PATH = r"D:\realestate\src\models\inference\scaler_x.pkl"
SCALER_Y_PATH = r"D:\realestate\src\models\inference\scaler_y.pkl"

# Ensure directories exist
os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)

print("1. Loading Data...")
house_df = pd.read_csv(DATA_PATH)

# Select Features (Columns 3 to 21 = 18 columns) and Target (Column 2 = Price)
X = house_df.iloc[:, 3:21].values
y = house_df.iloc[:, 2:3].values

# 2. Scaling
print("2. Scaling Data...")
scaler_x = MinMaxScaler()
X_scaled = scaler_x.fit_transform(X)

scaler_y = MinMaxScaler()
y_scaled = scaler_y.fit_transform(y)

# 3. Split Data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_scaled, test_size=0.25, random_state=42)

# 4. Building Model (Dynamic Input Dimension)
print(f"3. Building Model for {X.shape[1]} features...")
model = Sequential([
    # FIXED: Uses X.shape[1] (which is 18) instead of hardcoded 19
    Input(shape=(X.shape[1],)), 
    Dense(10, activation='relu'),
    Dense(10, activation='relu'),
    Dense(200, activation='relu'),
    Dense(200, activation='relu'),
    Dense(1, activation='linear')
])

model.compile(optimizer='adam', loss='mean_squared_error')

# 5. Train
print("4. Training Model...")
history = model.fit(X_train, y_train, epochs=100, batch_size=50, validation_data=(X_test, y_test), verbose=1)

# 6. Evaluate
print("5. Evaluating Performance...")
y_predict_scaled = model.predict(X_test)
y_predict_orig = scaler_y.inverse_transform(y_predict_scaled)
y_test_orig = scaler_y.inverse_transform(y_test)

r2 = r2_score(y_test_orig, y_predict_orig)
RMSE = np.sqrt(np.mean((y_test_orig - y_predict_orig) ** 2))

print("\n" + "="*30)
print(f" FINAL METRICS")
print(f" R2 Score: {r2:.4f}")
print(f" RMSE:     {RMSE:,.0f}")
print("="*30 + "\n")

# 7. Save
print(f"6. Saving files to {os.path.dirname(MODEL_SAVE_PATH)}...")
model.save(MODEL_SAVE_PATH)
joblib.dump(scaler_x, SCALER_X_PATH)
joblib.dump(scaler_y, SCALER_Y_PATH)
print("SUCCESS: Model and Scalers saved.")


# # Example dummy dataset (replace with your real data loading)
# df = pd.DataFrame({
#     'sqft': np.random.randint(500, 3000, 1000),
#     'bedrooms': np.random.randint(1, 5, 1000),
#     'bathrooms': np.random.randint(1, 4, 1000),
#     'price': np.random.randint(50000, 500000, 1000)
# })

# # Features and target
# X = df[['sqft', 'bedrooms', 'bathrooms']].values
# y = df['price'].values

# # Split
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# # Build small dense NN
# model = tf.keras.Sequential([
#     layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
#     layers.Dropout(0.2),
#     layers.Dense(32, activation='relu'),
#     layers.Dense(1)
# ])

# model.compile(optimizer='adam', loss='mse', metrics=['mae'])
# model.fit(X_train, y_train, epochs=30, batch_size=16, validation_split=0.2)

# # Evaluate
# loss, mae = model.evaluate(X_test, y_test)
# print(f"Test MAE: {mae}")

# # Save model locally
# model.save('price_prediction_model')



