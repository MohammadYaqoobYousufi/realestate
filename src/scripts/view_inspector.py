import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIG ---
DB_URL = "postgresql://postgres:postgreSQL@localhost:5432/realestate_db"
engine = create_engine(DB_URL)

VIEWS_TO_CHECK = [
    'geography_columns', 
    'geometry_columns', 
    'v_ai_readiness_audit', 
    'v_neighborhood_intelligence'
]

def inspect_views():
    print("🔭 ANALYZING TARGET VIEWS...\n")
    
    for view in VIEWS_TO_CHECK:
        print(f"VIEW: {view.upper()}")
        print("=" * 40)
        
        try:
            with engine.connect() as conn:
                # 1. Get Row Count
                count = conn.execute(text(f"SELECT COUNT(*) FROM {view}")).scalar()
                print(f"📊 Status: {count:,} records found.")

                # 2. Get Column Schema (Sample)
                sample = pd.read_sql(text(f"SELECT * FROM {view} LIMIT 1"), conn)
                print(f"🧬 Columns: {sample.columns.tolist()}")

                # 3. Get the View Definition (The SQL Logic behind it)
                # This helps us see how neighborhood intelligence is calculated
                definition = conn.execute(text(f"SELECT pg_get_viewdef('{view}', true)")).scalar()
                if definition:
                    print(f"📝 Definition:\n{definition.strip()}")
                else:
                    print("📝 Definition: System view (No manual SQL definition)")
                
        except Exception as e:
            print(f"⚠️  Could not access {view}: {e}")
        
        print("-" * 40 + "\n")

if __name__ == "__main__":
    inspect_views()