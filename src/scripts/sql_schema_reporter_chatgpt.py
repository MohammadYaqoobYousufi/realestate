from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

# ==========================================================
# CONFIG
# ==========================================================
DB_URL = "postgresql://postgres:postgreSQL@localhost:5432/realestate_db"
engine = create_engine(DB_URL, future=True)

SEPARATOR = "=" * 60


# ==========================================================
# HELPERS
# ==========================================================
def get_estimated_row_counts(conn):
    """
    Fast row count estimates using pg_class
    """
    sql = """
    SELECT
        relname AS name,
        reltuples::BIGINT AS rows
    FROM pg_class
    WHERE relkind IN ('r', 'v')
      AND relnamespace = 'public'::regnamespace;
    """
    return {row.name: row.rows for row in conn.execute(text(sql))}


def get_index_definitions(conn, table):
    """
    Returns full CREATE INDEX definitions (handles spatial & expression indexes)
    """
    sql = """
    SELECT
        i.relname AS index_name,
        pg_get_indexdef(ix.indexrelid) AS definition
    FROM pg_class t
    JOIN pg_index ix ON t.oid = ix.indrelid
    JOIN pg_class i ON i.oid = ix.indexrelid
    WHERE t.relname = :table;
    """
    return {
        row.index_name: row.definition
        for row in conn.execute(text(sql), {"table": table})
    }


# ==========================================================
# MAIN AUDIT
# ==========================================================
def run_comprehensive_audit():
    print("🔍 INITIALIZING MASTER SQL AUDIT...")
    print(SEPARATOR)

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    views = inspector.get_view_names()

    with engine.connect() as conn:

        # --------------------------------------------------
        # TABLE SUMMARY
        # --------------------------------------------------
        print("\n📊 TABLE SUMMARY (Estimated Rows)")
        print(f"{'Table Name':<30} | {'Rows':>12} | Type")
        print("-" * 60)

        row_counts = get_estimated_row_counts(conn)

        for table in tables:
            rows = row_counts.get(table, "N/A")
            print(f"{table:<30} | {str(rows):>12} | Table")

        for view in views:
            rows = row_counts.get(view, "N/A")
            print(f"{view:<30} | {str(rows):>12} | View")

        # --------------------------------------------------
        # COLUMN & CONSTRAINT DNA
        # --------------------------------------------------
        print("\n🧬 COLUMN & CONSTRAINT DNA")

        for table in tables:
            print(f"\nTABLE: {table.upper()}")
            print("-" * 40)

            try:
                columns = inspector.get_columns(table)
                pk_cols = set(
                    inspector.get_pk_constraint(table).get("constrained_columns", [])
                )
                fks = inspector.get_foreign_keys(table)

                fk_map = {
                    col: f"{fk['referred_table']}.{fk['referred_columns'][0]}"
                    for fk in fks
                    for col in fk["constrained_columns"]
                }

                for col in columns:
                    name = col["name"]
                    dtype = str(col["type"])
                    nullable = "NULL" if col["nullable"] else "NOT NULL"
                    pk = "[PK]" if name in pk_cols else ""
                    fk = f"-> FK({fk_map[name]})" if name in fk_map else ""

                    print(
                        f"  - {name:<22} {dtype:<18} {nullable:<10} {pk} {fk}"
                    )

            except SQLAlchemyError as e:
                print(f"  ⚠️ Unable to inspect table {table}: {e}")

        # --------------------------------------------------
        # INDEX & PERFORMANCE MAP
        # --------------------------------------------------
        print("\n⚡ INDEX & PERFORMANCE MAP")

        for table in tables:
            indexes = inspector.get_indexes(table)
            if not indexes:
                continue

            index_defs = get_index_definitions(conn, table)

            print(f"  [{table}]")
            for idx in indexes:
                name = idx["name"]
                col_names = idx.get("column_names") or []

                if any(c is None for c in col_names):
                    cols = index_defs.get(name, "<expression / spatial index>")
                else:
                    cols = f"({', '.join(col_names)})"

                unique = "UNIQUE" if idx.get("unique") else ""
                print(f"    └─ {name}: {cols} {unique}")

        # --------------------------------------------------
        # VIEW DEFINITIONS
        # --------------------------------------------------
        if views:
            print("\n🖼️ VIEW DEFINITIONS")

            for view in views:
                try:
                    sql = text("SELECT pg_get_viewdef(:view, true)")
                    definition = conn.execute(sql, {"view": view}).scalar()

                    print(f"\nVIEW: {view}")
                    print(definition.strip())

                except SQLAlchemyError as e:
                    print(f"\nVIEW: {view}")
                    print(f"  ⚠️ Unable to fetch definition: {e}")

    print("\n" + SEPARATOR)
    print("🏁 AUDIT COMPLETE.")


# ==========================================================
# ENTRY POINT
# ==========================================================
if __name__ == "__main__":
    run_comprehensive_audit()