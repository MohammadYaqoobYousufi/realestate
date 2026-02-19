import pandas as pd
import numpy as np
import psycopg2
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# -------------------------
# DATABASE CONNECTION
# -------------------------
conn = psycopg2.connect(
    dbname="realestate_db",
    user="postgres",
    password="postgreSQL",
    host="localhost",
    port="5432"
)

query = """
SELECT target_year, target_price,
       building_age, age_squared,
       land_size_sm, log_land_size,
       policy_rate_lag1,
       permit_count, avg_crime_rate,
       population, dwellings,
       population_per_dwelling,
       permits_per_capita, crime_per_capita,
       lag_price_1yr, lag_price_2yr,
       price_growth_1yr, price_growth_3yr,
       price_volatility_3yr,
       property_type,
       land_use_designation
FROM feature_store.v_training_enriched
WHERE target_year BETWEEN 2015 AND 2024;
"""

df = pd.read_sql(query, conn)

# -------------------------
# TARGET
# -------------------------
y = df["target_price"]

# Log-transform target (institutional standard)
y = np.log1p(y)

# -------------------------
# FEATURES
# -------------------------
numerical_features = [
    "building_age", "age_squared",
    "land_size_sm", "log_land_size",
    "policy_rate_lag1",
    "permit_count", "avg_crime_rate",
    "population", "dwellings",
    "population_per_dwelling",
    "permits_per_capita", "crime_per_capita",
    "lag_price_1yr", "lag_price_2yr",
    "price_growth_1yr", "price_growth_3yr",
    "price_volatility_3yr"
]

categorical_features = [
    "property_type",
    "land_use_designation",
    "comm_code"
]

X = df[numerical_features + categorical_features]

# -------------------------
# TIME-BASED SPLIT
# -------------------------
train = df[df.target_year <= 2022]
val   = df[df.target_year == 2023]
test  = df[df.target_year == 2024]

X_train = train[numerical_features + categorical_features]
y_train = np.log1p(train["target_price"])

X_val = val[numerical_features + categorical_features]
y_val = np.log1p(val["target_price"])

X_test = test[numerical_features + categorical_features]
y_test = np.log1p(test["target_price"])

# -------------------------
# PIPELINE
# -------------------------
preprocessor = ColumnTransformer(
    transformers=[
        ("num", "passthrough", numerical_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ]
)

model = ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=5000)

pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("model", model)
])

pipeline.fit(X_train, y_train)

# -------------------------
# VALIDATION METRICS
# -------------------------
val_preds = pipeline.predict(X_val)
val_rmse = np.sqrt(mean_squared_error(y_val, val_preds))
val_mae = mean_absolute_error(y_val, val_preds)

print("Validation RMSE (log):", val_rmse)
print("Validation MAE (log):", val_mae)

# -------------------------
# TEST METRICS
# -------------------------
test_preds = pipeline.predict(X_test)
test_rmse = np.sqrt(mean_squared_error(y_test, test_preds))
test_mae = mean_absolute_error(y_test, test_preds)

print("Test RMSE (log):", test_rmse)
print("Test MAE (log):", test_mae)