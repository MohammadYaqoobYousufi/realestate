import os
import pandas as pd
from sqlalchemy import create_engine, inspect, text
# System Health Check Script for Real Estate Valuation System


# --- CONFIG ---
PROJECT_ROOT = r"D:\realestate"
DB_URL = "postgresql://postgres:postgreSQL@localhost:5432/realestate_db"

def run_diagnostics():
    print("🩺 STARTING SYSTEM HEALTH CHECK...\n")
    
    # 1. File System Check
    print("--- 📂 FILE STRUCTURE ---")
    required = [
        "src/scripts/data_fetcher.py",
        "src/scripts/database_manager.py",
        "src/scripts/ai_brain.py",
        "data/raw/historical_assessments.csv"
    ]
    for f in required:
        path = os.path.join(PROJECT_ROOT, f)
        status = "✅" if os.path.exists(path) else "❌"
        print(f" {status} {f}")

    # 2. Database Connection & Schema
    print("\n--- 🗄️ DATABASE VITAL SIGNS ---")
    try:
        engine = create_engine(DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        core_tables = ["property_master", "assessment_history", "property_analytics", "macro_rates"]
        for t in core_tables:
            if t in tables:
                count = pd.read_sql(f"SELECT COUNT(*) FROM {t}", engine).iloc[0,0]
                print(f" ✅ {t.ljust(25)} : {count:,} rows")
            else:
                print(f" ❌ {t.ljust(25)} : MISSING")

        # 3. Data Quality Check
        print("\n--- 🔬 DATA QUALITY ---")
        with engine.connect() as conn:
            null_check = conn.execute(text("SELECT COUNT(*) FROM assessment_history WHERE assessed_value IS NULL")).scalar()
            print(f" Null Values in Assessment History: {null_check}")
            
            if "macro_rates" in tables:
                latest_rate = conn.execute(text("SELECT policy_rate FROM macro_rates ORDER BY date DESC LIMIT 1")).scalar()
                print(f" Latest Interest Rate Signal: {latest_rate}%")

    except Exception as e:
        print(f"❌ DATABASE CRITICAL ERROR: {e}")

    print("\n🏁 DIAGNOSTICS COMPLETE.")

if __name__ == "__main__":
    run_diagnostics()