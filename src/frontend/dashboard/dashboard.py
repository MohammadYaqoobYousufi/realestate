import streamlit as st
import numpy as np
import tensorflow as tf

model = tf.keras.models.load_model('price_prediction_model')

st.title("Real Estate Price Predictor")

sqft = st.number_input("Square Footage", min_value=300, max_value=10000, value=1500)
bedrooms = st.number_input("Bedrooms", min_value=1, max_value=10, value=3)
bathrooms = st.number_input("Bathrooms", min_value=1, max_value=10, value=2)

if st.button("Predict Price"):
    X = np.array([[sqft, bedrooms, bathrooms]])
    price = model.predict(X)
    st.success(f"Predicted Price: ${price[0][0]:,.2f}")
