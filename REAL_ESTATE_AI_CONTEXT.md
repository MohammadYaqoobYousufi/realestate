# Real Estate Agentic AI Platform — Context Snapshot

## 1. Mission
Build an Agentic AI-powered real estate intelligence platform
supporting AVM, CMA, forecasting, risk, and investment analytics.

## 2. Data Sources (Authoritative)
- assessment_history (2005–2025, ~10M rows)
- stage_current_assessments (2026, ~608k rows)
- property_master (~781k)
- building_permits (~483k)
- community_crime (~77k)
- community_census (306)
- macro_rates (daily)

## 3. Training Strategy
- Training window: 2015–2024 (5,275,590 rows)
- Validation: 2025
- Inference: 2026
- Point-in-time safe only

## 4. Feature Store
Schema: feature_store
Materialized views per year:
- mv_training_2015 → mv_training_2024
Union:
- mv_training_all

## 5. Status (LIVE)
- mv_training_2026 ✅ created
- mv_training_2026_clean ✅ created
- mv_training_2015 ⏳ building (started)

## 6. Rules
- Never join future data
- No ALTER on materialized views
- Always year-partition first

“Here is my project Context Snapshot:”

SQL 
is was running: 
CREATE MATERIALIZED VIEW feature_store.mv_training_2015 AS
SELECT
    h.roll_number::BIGINT                       AS roll_number,
    h.assessment_year                           AS target_year,
    h.assessed_value                            AS target_price,

    -- Point-in-time anchor
    make_date(h.assessment_year, 1, 1)          AS as_of_date,

    -- Property attributes (known before 2015)
    p.property_type,
    p.year_of_construction,
    (h.assessment_year - p.year_of_construction) AS building_age,
    p.land_size_sm,
    p.land_size_sf,
    p.land_use_designation,

    -- Neighborhood
    p.comm_code,
    p.comm_name,

    -- Macro (STRICTLY lagged)
    m.policy_rate                               AS policy_rate_lagged,

    -- Permits (lagged)
    COUNT(DISTINCT bp.permitnum)                AS permit_count,

    -- Crime (lagged)
    AVG(cc.crime_count)                         AS avg_crime_rate,

    -- Census (static)
    cn.res_cnt                                  AS population,
    cn.dwell_cnt                                AS dwellings

FROM assessment_history h

JOIN property_master p
  ON h.roll_number = p.roll_number

LEFT JOIN macro_rates m
  ON m.date < make_date(h.assessment_year, 1, 1)

LEFT JOIN building_permits bp
  ON upper(bp.communityname) = upper(p.comm_name)
 AND bp.issueddate < make_date(h.assessment_year, 1, 1)

LEFT JOIN community_crime cc
  ON upper(cc.community) = upper(p.comm_name)
 AND cc.year < h.assessment_year

LEFT JOIN community_census cn
  ON upper(cn.name) = upper(p.comm_name)

WHERE h.assessment_year = 2015

GROUP BY
    h.roll_number,
    h.assessment_year,
    h.assessed_value,
    p.property_type,
    p.year_of_construction,
    p.land_size_sm,
    p.land_size_sf,
    p.land_use_designation,
    p.comm_code,
    p.comm_name,
    m.policy_rate,
    cn.res_cnt,
    cn.dwell_cnt;