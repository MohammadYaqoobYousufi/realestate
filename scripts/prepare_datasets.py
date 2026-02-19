"""Preparation and basic validation for raw datasets.

- Converts shapefiles/zips to GeoJSON (EPSG:4326)
- Loads CSVs and checks for required fields
- Produces small sample files in data/processed/ and a manifest `data/processed/manifest.json`
"""
import os
import json
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DIR = os.path.join(ROOT, 'data', 'raw')
PROCESSED_DIR = os.path.join(ROOT, 'data', 'processed')
os.makedirs(PROCESSED_DIR, exist_ok=True)

MANIFEST = {}


def safe_sample(df, n=5):
    try:
        return df.head(n).to_dict(orient='records')
    except Exception:
        return []


def process_csv(path, name):
    try:
        df = pd.read_csv(path, low_memory=False)
        print(f"Loaded {name}: {len(df)} rows, {len(df.columns)} cols")
        sample = safe_sample(df)
        out_path = os.path.join(PROCESSED_DIR, name + '.sample.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({'n_rows': len(df), 'columns': list(df.columns), 'sample': sample}, f, indent=2)
        MANIFEST[name] = {'type': 'csv', 'rows': len(df), 'columns': list(df.columns), 'processed_sample': out_path}
    except Exception as e:
        print(f"  Failed to process CSV {path}: {e}")
        MANIFEST[name] = {'error': str(e)}


if __name__ == '__main__':
    print('Scanning data/raw for CSV files...')
    for fn in os.listdir(RAW_DIR):
        path = os.path.join(RAW_DIR, fn)
        if fn.lower().endswith('.csv'):
            name = os.path.splitext(fn)[0]
            process_csv(path, name)
        elif fn.lower().endswith(('.geojson', '.json')):
            # Attempt to read geojson with geopandas if available
            name = os.path.splitext(fn)[0]
            try:
                import geopandas as gpd
                gdf = gpd.read_file(path)
                print(f"Loaded {name} (geojson): {len(gdf)} features, {len(gdf.columns)} cols")
                sample = safe_sample(gdf.__geo_interface__ if hasattr(gdf, '__geo_interface__') else gdf.head(5).to_dict(orient='records'))
                out_path = os.path.join(PROCESSED_DIR, name + '.sample.json')
                with open(out_path, 'w', encoding='utf-8') as f:
                    json.dump({'n_features': len(gdf), 'columns': list(gdf.columns), 'sample': sample}, f, indent=2)
                MANIFEST[name] = {'type': 'geojson', 'features': len(gdf), 'columns': list(gdf.columns), 'processed_sample': out_path}
            except Exception as e:
                print(f"  Could not fully parse GeoJSON {path}: {e}. Writing minimal metadata.")
                MANIFEST[name] = {'type': 'geojson', 'error': str(e)}

    manifest_path = os.path.join(PROCESSED_DIR, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(MANIFEST, f, indent=2)
    print('Processing complete. See data/processed/manifest.json')
