import streamlit as st
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Real Estate Predictor", layout="centered")

# --- LOAD ASSETS ---
@st.cache_resource
def load_assets():
    model = load_model(r'D:\realestate\src\models\inference\house_price_model.h5')
    scaler_x = joblib.load(r'D:\realestate\src\models\inference\scaler_x.pkl')
    scaler_y = joblib.load(r'D:\realestate\src\models\inference\scaler_y.pkl')
    return model, scaler_x, scaler_y

try:
    model, scaler_x, scaler_y = load_assets()
    st.success("AI Brain Loaded Successfully!")
except Exception as e:
    st.error(f"Error loading model files: {e}")
    st.stop()

# --- USER INTERFACE ---
st.title("🏡 Real Estate Price Prediction AI")
st.write("Adjust the features below to get an instant valuation.")

col1, col2 = st.columns(2)

with col1:
    bedrooms = st.number_input("Bedrooms", min_value=1, max_value=10, value=3)
    bathrooms = st.number_input("Bathrooms", min_value=1.0, max_value=8.0, value=2.0, step=0.25)
    sqft_living = st.slider("Living Area (Sqft)", 500, 10000, 2000)
    floors = st.selectbox("Floors", [1, 1.5, 2, 2.5, 3])

with col2:
    waterfront = st.radio("Waterfront View?", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
    condition = st.slider("Condition (1-5)", 1, 5, 3)
    grade = st.slider("Grade (1-13)", 1, 13, 7)
    yr_built = st.number_input("Year Built", 1900, 2026, 2000)

# --- PREDICTION LOGIC ---
# Note: We need to match the 18 features exactly as trained
if st.button("Calculate Property Value"):
    # Creating a dummy array for the 18 features (filling missing ones with averages/zeros)
    # Mapping: [bedrooms, bathrooms, sqft_living, sqft_lot, floors, waterfront, view, condition, grade, sqft_above, sqft_basement, yr_built, yr_renovated, zipcode, lat, long, sqft_living15, sqft_lot15]
    input_data = np.array([[
        bedrooms, bathrooms, sqft_living, 5000, floors, waterfront, 0, condition, grade, 
        sqft_living, 0, yr_built, 0, 98001, 47.5, -122.2, sqft_living, 5000
    ]])
    
    # Scale, Predict, and Inverse Scale
    input_scaled = scaler_x.transform(input_data)
    prediction_scaled = model.predict(input_scaled)
    final_price = scaler_y.inverse_transform(prediction_scaled)[0][0]
    
    st.metric(label="Estimated Market Value", value=f"${final_price:,.2f}")
    st.balloons()