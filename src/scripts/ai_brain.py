import pandas as pd
from sqlalchemy import create_engine, text
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Role: The "Intelligence". Integrates Trains the XGBoost model and pushes predictions.
DB_URL = "postgresql://postgres:postgreSQL@localhost:5432/realestate_db"
engine = create_engine(DB_URL)
MODEL_DIR = r"D:\realestate\src\models\inference"

def train_and_predict():
    print("🤖 STARTING AI TRAINING PIPELINE...")
    
    # 1. Load Data from View
    query = "SELECT * FROM v_model_training_set"
    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        print(f"❌ Error reading view: {e}")
        return

    if df.empty:
        print("❌ Training set is empty. Run database_manager.py first.")
        return

    # 2. Feature Engineering
    print(f"📊 Training on {len(df)} records...")
    le = LabelEncoder()
    df['property_type_enc'] = le.fit_transform(df['property_type'].astype(str))
    df = df.fillna(0) # Simple imputation for demo

    features = ['year_of_construction', 'land_size_sf', 'property_type_enc', 'avg_interest_rate']
    X = df[features]
    y = df['current_market_value']

    # 3. Train XGBoost
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBRegressor(n_estimators=100, learning_rate=0.1, n_jobs=-1)
    model.fit(X_train, y_train)

    # 4. Evaluate
    preds = model.predict(X_test)
    mape = mean_absolute_percentage_error(y_test, preds)
    print(f"✅ Model Accuracy: {100 - (mape*100):.2f}%")

    # 5. Save Model
    if not os.path.exists(MODEL_DIR): os.makedirs(MODEL_DIR)
    joblib.dump(model, os.path.join(MODEL_DIR, "avm_xgboost.pkl"))

    # 6. Generate Predictions & Push to DB
    print("🔮 Generating 2026 Predictions...")
    # Simulate next year by adding 1 year to age logic if needed, or just predicting current value delta
    full_preds = model.predict(X)
    
    results = pd.DataFrame({
        'roll_number': df['roll_number'],
        'predicted_market_value': full_preds
    })
    
    print("💾 Saving predictions to 'property_analytics'...")
    results.to_sql('temp_analytics', engine, if_exists='replace', index=False)
    
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO property_analytics (roll_number, predicted_market_value, valuation_date)
            SELECT roll_number, predicted_market_value, CURRENT_DATE FROM temp_analytics
            ON CONFLICT (roll_number) DO UPDATE SET
                predicted_market_value = EXCLUDED.predicted_market_value,
                valuation_date = CURRENT_DATE;
        """))
    print("🏁 AI PIPELINE FINISHED.")

if __name__ == "__main__":
    train_and_predict()