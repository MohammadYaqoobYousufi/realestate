# -- types in property_master
from tkinter import ON


SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'  -- or your schema for property_master
  AND table_name = 'property_master'
ORDER BY ordinal_position;

# -- types in training view
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'feature_store'
  AND table_name = 'v_training_model_ready'
ORDER BY ordinal_position;

# -- Quick check: how many rows match when we normalize both sides to digits-only strings?
SELECT
  count(*) AS total_rows,
  count(pm.roll_number) AS matched_by_normalized
FROM feature_store.v_training_model_ready t
LEFT JOIN property_master pm
  ON pm.roll_number = t.roll_number::text;
  
SELECT
  count(*) AS total,
  count(*) FILTER (WHERE pm.roll_number IS NULL) AS not_matched_by_direct_join,
  count(*) FILTER (WHERE pm.roll_number IS NULL) * 100.0 / count(*) AS pct_not_matched
FROM feature_store.v_training_model_ready t
LEFT JOIN property_master pm
  ON pm.roll_number = t.roll_number::text;


# -- sample from training view (problem side)
SELECT DISTINCT t.roll_number::text AS training_roll_number
FROM feature_store.v_training_model_ready t
LIMIT 20;

# -- sample from property_master
SELECT DISTINCT pm.roll_number AS property_master_roll_number
FROM property_master pm
LIMIT 20;

# -- create mapping MV (safe; fast to drop)
CREATE MATERIALIZED VIEW feature_store.mv_rollkey_map AS
SELECT
  pm.roll_number AS pm_roll_number,
  regexp_replace(pm.roll_number, '\D', '', 'g') AS roll_norm
FROM property_master pm
WHERE pm.roll_number IS NOT NULL;

CREATE INDEX idx_mv_rollkey_map_roll_norm ON feature_store.mv_rollkey_map (roll_norm);

# -- test join count using mapping
SELECT
  count(*) AS total,
  count(m.pm_roll_number) AS matched_via_map
FROM feature_store.v_training_model_ready t
LEFT JOIN feature_store.mv_rollkey_map m
  ON regexp_replace(t.roll_number::text, '\D', '', 'g') = m.roll_norm;



CREATE OR REPLACE VIEW feature_store.v_training_model_ready_with_structural AS
SELECT
  t.*,
  pm.property_type,
  pm.year_of_construction,
  pm.land_size_sm,
  pm.land_use_designation,
  pm.comm_code AS pm_comm_code
FROM feature_store.v_training_model_ready t
LEFT JOIN property_master pm
  ON pm.roll_number = t.roll_number::text;

SELECT
  COUNT(*) AS total,
  COUNT(property_type) AS property_type_non_null,
  COUNT(land_size_sm) AS land_size_non_null
FROM feature_store.v_training_model_ready_with_structural;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_master_rollnorm
  ON property_master ( (regexp_replace(roll_number, '\D', '', 'g')) );