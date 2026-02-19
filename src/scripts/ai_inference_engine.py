import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
import numpy as np

# --- CONFIGURATION ---
DB_URL = "postgresql://postgres:postgreSQL@localhost:5432/realestate_db"
engine = create_engine(DB_URL)

def run_ai_inference():
    print("🤖 Loading Features from Materialized View...")
    # Pulling the 'Golden Dataset'
    query = "SELECT * FROM mv_ml_training_data WHERE geom IS NOT NULL"
    df = pd.read_sql(query, engine)
    
    if df.empty:
        print("❌ Error: No data found in mv_ml_training_data. Refresh the view first!")
        return

    # 1. Pre-processing: Convert categorical data to numbers
    # AI can't read 'Residential', it needs '1'
    df_encoded = pd.get_dummies(df, columns=['property_type'])
    
    # 2. Define Features (X) and Target (y)
    # We are training the AI to predict 'assessed_value'
    features = ['building_age', 'land_size_sf', 'interest_rate_at_valuation']
    # Add the encoded property types back into features
    features += [c for c in df_encoded.columns if 'property_type_' in c]
    
    X = df_encoded[features].fillna(0)
    y = df_encoded['assessed_value']

    print(f"🧠 Training Random Forest Model on {len(df)} properties...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    print("🔮 Generating 2026 Market Predictions...")
    # For prediction, we simulate a slight interest rate change (e.g. current rate)
    X_pred = X.copy()
    X_pred['building_age'] += 1 # Prediction for next year
    
    predictions = model.predict(X_pred)

    # 3. Save to property_analytics
    results = pd.DataFrame({
        'roll_number': df['roll_number'],
        'predicted_market_value': predictions,
        'neighborhood_appreciation_rate': (predictions - df['assessed_value']) / df['assessed_value']
    })

    print("📥 Updating Property Analytics Table...")
    results.to_sql('temp_predictions', engine, if_exists='replace', index=False)
    
    # SQL Update to merge the AI results into the master analytics table
    with engine.begin() as conn:
        conn.execute("""
            UPDATE property_analytics pa
            SET predicted_market_value = tp.predicted_market_value,
                neighborhood_appreciation_rate = tp.neighborhood_appreciation_rate
            FROM temp_predictions tp
            WHERE pa.roll_number = tp.roll_number;
        """)
    
    print("✅ Success! The platform is now 'Intelligent'.")

if __name__ == "__main__":
    run_ai_inference()