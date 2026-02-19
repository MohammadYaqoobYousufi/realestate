# train_and_register_lgb.py (robust, schema-drift tolerant)
import os, json, hashlib, joblib
from datetime import datetime,timezone
import numpy as np
import pandas as pd
import sqlalchemy as sa
import lightgbm as lgb
import shap
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------
DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgreSQL@localhost:5432/realestate_db")
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "model_artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

MODEL_NAME = os.getenv("MODEL_NAME", "avm_lgb_v1")
CREATED_BY = os.getenv("USER", "automation")

# canonical feature lists (expected — we will intersect with actual columns)
NUMERICAL = [
    "building_age", "age_squared",
    "land_size_sm", "log_land_size",
    "policy_rate_lag1", "permit_count",
    "avg_crime_rate", "population_per_dwelling",
    "permits_per_capita", "crime_per_capita",
    "price_growth_1yr", "price_volatility_3yr",
    "lag_price_1yr", "lag_price_2yr"
]

CATEGORICAL = [
    "property_type",
    "land_use_designation",
    "comm_code"
]

EXTRACTION_SQL = f"""
SELECT target_year, target_price,
       {", ".join(NUMERICAL)},
       {", ".join(CATEGORICAL)}
FROM feature_store.v_training_enriched
WHERE target_year BETWEEN 2015 AND 2024
  AND target_price IS NOT NULL
  AND target_price > 0
ORDER BY target_year;
"""

# -------------------------------------------------------
# UTILS
# -------------------------------------------------------
def dataset_hash(df, numeric_cols):
    import hashlib as _hashlib
    h = _hashlib.sha256()
    h.update(",".join(df.columns).encode())
    h.update(str(df.shape).encode())
    for c in sorted(numeric_cols):
        if c in df.columns:
            v = float(df[c].fillna(0).mean())
            h.update(f"{c}:{v:.8f}".encode())
    return h.hexdigest()

def mdape(y_true, y_pred):
    return np.median(np.abs((y_true - y_pred) / y_true)) * 100

def ppe(y_true, y_pred, pct=0.10):
    return np.mean(np.abs((y_true - y_pred) / y_true) <= pct) * 100

def cod(y_true, y_pred):
    ratios = y_pred / y_true
    med = np.median(ratios)
    return (100.0 / med) * np.mean(np.abs(ratios - med))

def prd(y_true, y_pred):
    mean_ratio = np.mean(y_pred / y_true)
    wtd_mean_ratio = np.sum(y_pred) / np.sum(y_true)
    return mean_ratio / wtd_mean_ratio

def eval_d(y_true, y_pred, label):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    md = mdape(y_true, y_pred)
    p10 = ppe(y_true, y_pred, 0.10)
    c = cod(y_true, y_pred)
    p = prd(y_true, y_pred)

    print(f"\n--- {label} ---")
    print(f"RMSE : {rmse:,.2f}")
    print(f"MAE  : {mae:,.2f}")
    print(f"MdAPE: {md:.2f}%")
    print(f"PPE10: {p10:.2f}%")
    print(f"COD  : {c:.2f}")
    print(f"PRD  : {p:.3f}")

    return {"rmse": rmse, "mae": mae, "mdape": md,
            "ppe10": p10, "cod": c, "prd": p}

# -------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------
engine = sa.create_engine(DB_URL)

with engine.connect() as conn:
    df = pd.read_sql(EXTRACTION_SQL, conn)

print("Rows loaded:", len(df))

# DEBUG: show exact columns returned by SQL (helps debug schema drift)
print("DEBUG: columns returned by SQL:")
print(df.columns.tolist())

# -------------------------------------------------------
# ADJUST: detect which canonical features actually exist
# -------------------------------------------------------
available_numerical = [c for c in NUMERICAL if c in df.columns]
missing_numerical = [c for c in NUMERICAL if c not in available_numerical]
if missing_numerical:
    print("WARNING: Missing numerical columns (will be skipped):", missing_numerical)

available_categorical = [c for c in CATEGORICAL if c in df.columns]
missing_categorical = [c for c in CATEGORICAL if c not in available_categorical]
if missing_categorical:
    print("WARNING: Missing categorical columns (will be skipped):", missing_categorical)

if len(available_numerical) == 0 and len(available_categorical) == 0:
    raise RuntimeError("No features available for training. Check feature store view.")

# -------------------------------------------------------
# OPTIONAL MEMORY SAFE SAMPLING
# -------------------------------------------------------
MAX_ROWS = int(os.getenv("MAX_ROWS_FULL_TRAIN", "4500000"))
if len(df) > MAX_ROWS:
    frac = MAX_ROWS / len(df)
    df = df.sample(frac=frac, random_state=42).sort_values("target_year").reset_index(drop=True)
    print(f"Sampled dataset to {len(df)} rows (frac={frac:.3f})")

# -------------------------------------------------------
# CLEANING (defensive)
# -------------------------------------------------------
df = df.dropna(axis=1, how="all")  # drop any fully-empty columns

# Recompute available columns after dropna
available_numerical = [c for c in NUMERICAL if c in df.columns]
available_categorical = [c for c in CATEGORICAL if c in df.columns]

# Warn for missing cols (audit)
missing_numerical = [c for c in NUMERICAL if c not in available_numerical]
missing_categorical = [c for c in CATEGORICAL if c not in available_categorical]
if missing_numerical:
    print("WARNING: Missing numerical columns (will be skipped):", missing_numerical)
if missing_categorical:
    print("WARNING: Missing categorical columns (will be skipped):", missing_categorical)

# Fill numeric nulls only for columns that exist
for col in available_numerical:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

# Ensure categorical columns exist and have correct dtype
for col in available_categorical:
    if col in df.columns:
        df[col] = df[col].astype("category")

# -------------------------------------------------------
# SCALING (only on available numeric cols)
# -------------------------------------------------------
scaler = RobustScaler()
if len(available_numerical) > 0:
    df[available_numerical] = scaler.fit_transform(df[available_numerical])

# -------------------------------------------------------
# SPLIT
# -------------------------------------------------------
train = df[df.target_year <= 2022].reset_index(drop=True)
val   = df[df.target_year == 2023].reset_index(drop=True)
test  = df[df.target_year == 2024].reset_index(drop=True)

if len(val) == 0 or len(test) == 0:
    raise ValueError("Validation or Test set is empty. Check data coverage.")

# -------------------------------------------------------
# TARGET (log for training stability)
# -------------------------------------------------------
y_train_log = np.log1p(train["target_price"].values)
y_val_log   = np.log1p(val["target_price"].values)

# -------------------------------------------------------
# FEATURES (available only)
# Recompute feature columns from available lists
feature_cols = available_numerical + available_categorical

# Safety check: must have at least one feature
if len(feature_cols) == 0:
    raise RuntimeError("No feature columns are available after cleaning. Aborting. Check your feature store view or EXTRACTION_SQL.")

X_train = train[feature_cols]
X_val   = val[feature_cols]
X_test  = test[feature_cols]

categorical_feature = [c for c in available_categorical if c in X_train.columns]

# -------------------------------------------------------
# LIGHTGBM DATASETS
# -------------------------------------------------------
dtrain = lgb.Dataset(X_train, label=y_train_log, categorical_feature=categorical_feature, free_raw_data=False)
dval   = lgb.Dataset(X_val, label=y_val_log, categorical_feature=categorical_feature, reference=dtrain, free_raw_data=False)

# -------------------------------------------------------
# MODEL (tuned for laptop)
# -------------------------------------------------------
lgb_params = {
    "objective": "regression",
    "metric": "rmse",
    "learning_rate": 0.05,
    "num_leaves": 64,
    "min_data_in_leaf": 50,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "verbosity": -1,
    "seed": 42,
    "n_jobs": max(1, int(os.cpu_count() * 0.6))
}

callbacks = [
    lgb.early_stopping(stopping_rounds=50),
    lgb.log_evaluation(period=50)
]

bst = lgb.train(
    lgb_params,
    dtrain,
    num_boost_round=2000,
    valid_sets=[dtrain, dval],
    valid_names=["train", "valid"],
    callbacks=callbacks
)

# -------------------------------------------------------
# PREDICTIONS (dollar scale)
# -------------------------------------------------------
val_preds = np.expm1(bst.predict(X_val, num_iteration=bst.best_iteration))
test_preds = np.expm1(bst.predict(X_test, num_iteration=bst.best_iteration))

val_true = val["target_price"].values.astype(float)
test_true = test["target_price"].values.astype(float)

# robust masking to guarantee numeric, finite, positive targets for metrics
val_mask = np.isfinite(val_true) & np.isfinite(val_preds) & (val_true > 0)
test_mask = np.isfinite(test_true) & np.isfinite(test_preds) & (test_true > 0)

print(f"Validation rows kept: {val_mask.sum()}/{len(val_mask)}")
print(f"Test rows kept: {test_mask.sum()}/{len(test_mask)}")

if val_mask.sum() == 0 or test_mask.sum() == 0:
    raise RuntimeError("No valid rows for evaluation after masking. Investigate data quality.")

metrics_val = eval_d(val_true[val_mask], val_preds[val_mask], "VALIDATION(2023)")
metrics_test = eval_d(test_true[test_mask], test_preds[test_mask], "TEST(2024)")

# -------------------------------------------------------
# SHAP (sample safely)
# -------------------------------------------------------
sample_n = min(100000, X_train.shape[0])
if sample_n > 0:
    sample_idx = np.random.choice(X_train.shape[0], sample_n, replace=False)
    explainer = shap.TreeExplainer(bst)
    shap_vals = explainer.shap_values(X_train.iloc[sample_idx])
    shap_mean = np.mean(np.abs(shap_vals), axis=0)
    shap_df = pd.DataFrame({
        "feature": bst.feature_name(),
        "mean_abs_shap": shap_mean
    }).sort_values("mean_abs_shap", ascending=False)
else:
    shap_df = pd.DataFrame(columns=["feature", "mean_abs_shap"])

# -------------------------------------------------------
# SAVE ARTIFACTS
# -------------------------------------------------------
timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
artifact_path = os.path.join(ARTIFACT_DIR, f"{MODEL_NAME}_{timestamp}")
os.makedirs(artifact_path, exist_ok=True)

joblib.dump(bst, os.path.join(artifact_path, "model_lightgbm.joblib"))
joblib.dump(scaler, os.path.join(artifact_path, "scaler.joblib"))
shap_path = os.path.join(artifact_path, "shap_summary.csv")
shap_df.to_csv(shap_path, index=False)

# -------------------------------------------------------
# REGISTER MODEL
# -------------------------------------------------------
ds_hash = dataset_hash(df, available_numerical)

meta = {
    "model_name": MODEL_NAME,
    "model_version": timestamp,
    "artifact_path": artifact_path,
    "created_by": CREATED_BY,
    "training_start": pd.to_datetime(f"{int(train.target_year.min())}-01-01").date(),
    "training_end": pd.to_datetime(f"{int(train.target_year.max())}-12-31").date(),
    "feature_list": json.dumps(feature_cols),
    "params": json.dumps(lgb_params),
    "metrics": json.dumps({"validation": metrics_val, "test": metrics_test}),
    "dataset_rows": int(len(df)),
    "dataset_query": EXTRACTION_SQL,
    "dataset_hash": ds_hash,
    "notes": "LGBM trained on log1p(target); metrics in dollar scale; schema-drift tolerant run"
}

with engine.begin() as conn:
    result = conn.execute(sa.text("""
        INSERT INTO feature_store.model_registry
        (model_name, model_version, artifact_path, created_by,
         training_start, training_end, feature_list, params,
         metrics, dataset_rows, dataset_query, dataset_hash, notes)
        VALUES (:model_name, :model_version, :artifact_path, :created_by,
                :training_start, :training_end, :feature_list, :params,
                :metrics, :dataset_rows, :dataset_query, :dataset_hash, :notes)
        RETURNING model_id;
    """), meta)
    model_id = int(result.scalar())

print("\nSUCCESS. model_id:", model_id)
print("Artifacts stored at:", artifact_path)