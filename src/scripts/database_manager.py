import pandas as pd
from sqlalchemy import create_engine, text
import os
import sys
import json
# Role: The "Architect". Handles Schema Creation, Ingestion, and Global Merges.

# --- CONFIG ---
DB_URL = "postgresql://postgres:postgreSQL@localhost:5432/realestate_db"
DATA_DIR = r"D:\realestate\data\raw"
engine = create_engine(DB_URL)

def setup_database_schema():
    print("🏗️  Initializing Database Schema (Tables & Extensions)...")
    schema_sql = """
    CREATE EXTENSION IF NOT EXISTS postgis;
    
    -- 1. Property Master (Physical)
    CREATE TABLE IF NOT EXISTS property_master (
        roll_number TEXT PRIMARY KEY,
        address TEXT,
        comm_code TEXT,
        comm_name TEXT,
        property_type TEXT,
        year_of_construction INT,
        land_use_designation TEXT,
        sub_property_use TEXT,
        land_size_sf NUMERIC,
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        location GEOMETRY(Point, 4326),
        cpid BIGINT,
        -- Conditionals (for future AI expansion)
        total_rooms INT, bedrooms INT, bathrooms FLOAT, is_waterfront BOOLEAN
    );

    -- 2. Assessment History (Financial)
    CREATE TABLE IF NOT EXISTS assessment_history (
        id SERIAL PRIMARY KEY,
        roll_number TEXT REFERENCES property_master(roll_number) ON DELETE CASCADE,
        assessment_year INT,
        assessed_value NUMERIC,
        assessment_class TEXT,
        UNIQUE (roll_number, assessment_year)
    );

    -- 3. Context Layers (Supply/Crime/Macro)
    CREATE TABLE IF NOT EXISTS building_permits (
        id SERIAL PRIMARY KEY, permit_num TEXT, status TEXT, applied_date DATE,
        est_project_cost NUMERIC, community_name TEXT, original_address TEXT
    );
    CREATE TABLE IF NOT EXISTS community_crime (
        id SERIAL PRIMARY KEY, community_name TEXT, category TEXT, 
        crime_count INT, year INT, month TEXT
    );
    CREATE TABLE IF NOT EXISTS macro_rates (
        date DATE PRIMARY KEY, policy_rate DOUBLE PRECISION
    );
    CREATE TABLE IF NOT EXISTS community_census (
        comm_code TEXT, name TEXT, res_cnt INT, dwell_cnt INT, ownshp_cnt INT
    );

    -- 4. AI Analytics (Predictions)
    CREATE TABLE IF NOT EXISTS property_analytics (
        roll_number TEXT REFERENCES property_master(roll_number) PRIMARY KEY,
        predicted_market_value NUMERIC,
        valuation_date DATE DEFAULT CURRENT_DATE,
        confidence_interval_low NUMERIC,
        confidence_interval_high NUMERIC,
        neighborhood_appreciation_rate FLOAT,
        fraud_risk_index FLOAT,
        deep_features JSONB
    );
    """
    with engine.connect() as conn:
        conn.execute(text(schema_sql))
        conn.commit()
    print("✅ Schema deployed.")

def ingest_file(file_name, table_name, mode='append'):
    path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(path):
        print(f"⏩ Skipping {file_name} (Not found)")
        return

    print(f"📥 Ingesting {file_name} -> {table_name}...")
    
    # Special handling for BoC JSON
    if file_name.endswith('.json') and table_name == 'macro_rates':
        with open(path, 'r') as f:
            data = json.load(f)
        obs = data.get('observations', [])
        rows = [{'date': o['d'], 'policy_rate': float(o['V80691311']['v'])} for o in obs]
        df = pd.DataFrame(rows)
    else:
        # Standard CSV
        chunk_iter = pd.read_csv(path, chunksize=50000, low_memory=False)
        for i, chunk in enumerate(chunk_iter):
            # Clean Columns
            chunk.columns = [c.lower().replace(' ', '_').replace('-', '_').strip() for c in chunk.columns]
            
            # Write to DB
            if_exists = 'replace' if i == 0 and mode == 'replace' else 'append'
            chunk.to_sql(table_name, engine, if_exists=if_exists, index=False)
            sys.stdout.write(f"\r   Processed {(i+1)*50000:,} rows...")
        print("")

def create_ai_views():
    print("🧠 Creating AI Training Views...")
    view_sql = """
    DROP VIEW IF EXISTS v_model_training_set;
    CREATE VIEW v_model_training_set AS
    SELECT 
        p.roll_number,
        p.year_of_construction,
        p.land_size_sf,
        p.property_type,
        h.assessed_value as current_market_value,
        c.res_cnt as population_density,
        (SELECT AVG(policy_rate) FROM macro_rates WHERE date > CURRENT_DATE - INTERVAL '1 year') as avg_interest_rate
    FROM property_master p
    JOIN assessment_history h ON p.roll_number = h.roll_number
    LEFT JOIN community_census c ON p.comm_code = c.comm_code
    WHERE h.assessment_year = 2025;
    """
    with engine.connect() as conn:
        conn.execute(text(view_sql))
        conn.commit()
    print("✅ View 'v_model_training_set' created.")

if __name__ == "__main__":
    setup_database_schema()
    
    # 1. Ingest Core Data
    ingest_file("current_assessments.csv", "stage_current_assessments", mode='replace')
    ingest_file("historical_assessments.csv", "historical_assessments", mode='replace') # Careful with massive files
    
    # 2. Ingest Context Layers
    ingest_file("interest_rates.json", "macro_rates", mode='replace')
    ingest_file("building_permits.csv", "building_permits", mode='replace')
    ingest_file("community_crime.csv", "community_crime", mode='replace')
    ingest_file("community_census.csv", "community_census", mode='replace')
    
    # 3. Global Merge & Views
    # (Insert your global merge SQL logic here if needed for staging -> master)
    create_ai_views()
    print("🏁 DATABASE HYDRATION COMPLETE.")