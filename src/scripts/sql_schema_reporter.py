import pandas as pd
from sqlalchemy import create_engine, text, inspect
import sys

# --- CONFIGURATION ---
DB_URL = "postgresql://postgres:postgreSQL@localhost:5432/realestate_db"
engine = create_engine(DB_URL)

def run_comprehensive_audit():
    print("🔍 INITIALIZING MASTER SQL AUDIT...")
    print("=" * 60)
    
    try:
        inspector = inspect(engine)
        
        # 1. TABLE SUMMARY & ROW COUNTS
        print("\n📊 TABLE SUMMARY")
        print(f"{'Table Name':<30} | {'Rows':>12} | {'Type'}")
        print("-" * 60)
        
        tables = inspector.get_table_names()
        views = inspector.get_view_names()
        
        with engine.connect() as conn:
            # Audit Tables
            for table in tables:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"{table:<30} | {count:12,} | Table")
            
            # Audit Views
            for view in views:
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {view}")).scalar()
                    print(f"{view:<30} | {count:12,} | View")
                except:
                    print(f"{view:<30} | {'ERROR':>12} | View (Check Definition)")

        # 2. DETAILED COLUMN & CONSTRAINT DNA
        print("\n🧬 COLUMN & CONSTRAINT DNA")
        for table in tables:
            print(f"\nTABLE: {table.upper()}")
            print("-" * 40)
            
            # Columns
            columns = inspector.get_columns(table)
            pk = inspector.get_pk_constraint(table).get('constrained_columns', [])
            fks = inspector.get_foreign_keys(table)
            
            for col in columns:
                name = col['name']
                dtype = str(col['type'])
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                tag = "[PK]" if name in pk else ""
                
                # Check if it's a Foreign Key
                fk_info = ""
                for fk in fks:
                    if name in fk['constrained_columns']:
                        fk_info = f"-> FK({fk['referred_table']}.{fk['referred_columns'][0]})"
                
                print(f"  - {name:<20} {dtype:<15} {nullable:<10} {tag} {fk_info}")

        # 3. INDEX & GEOSPATIAL AUDIT
        print("\n⚡ INDEX & PERFORMANCE MAP")
        for table in tables:
            indices = inspector.get_indexes(table)
            if indices:
                print(f"  [{table}]")
                for idx in indices:
                    cols = ", ".join(idx['column_names'])
                    unique = "(UNIQUE)" if idx['unique'] else ""
                    print(f"    └─ {idx['name']}: ({cols}) {unique}")

        # 4. VIEW DEFINITION CHECK
        if views:
            print("\n🖼️  VIEW DEFINITIONS (Calculated Logic)")
            for view in views:
                with engine.connect() as conn:
                    # Get the underlying query for the view
                    res = conn.execute(text(f"SELECT pg_get_viewdef('{view}', true)")).scalar()
                    print(f"\nVIEW: {view}")
                    print(res.strip())

    except Exception as e:
        print(f"❌ CRITICAL AUDIT FAILURE: {e}")

    print("\n" + "=" * 60)
    print("🏁 AUDIT COMPLETE. Please share the results above.")

if __name__ == "__main__":
    run_comprehensive_audit()