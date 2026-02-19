"""Validate presence and basic readability of required raw files for the Calgary datasets.

Checks:
- Files exist in data/raw
- For CSVs: can be read by pandas (head loaded)
- For GeoJSON: file is parseable (if geopandas available, use it)
- Writes a small validation report to data/raw/validation_report.json
"""
import os
import json
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DIR = os.path.join(ROOT, 'data', 'raw')
REQUIRED = [
    ('parcel_addresses.csv','Parcel Addresses (CSV)'),
    ('building_permits.csv','Building Permits (CSV)'),
    ('development_permits.csv','Development Permits (CSV)'),
    ('secondary_suites.csv','Calgary Secondary Suites (CSV)'),
    ('crime_by_community.csv','Crime by Community (CSV)'),
    ('statcan_census_ct_da.csv','StatsCan Census Profiles (CT/DA)'),
    ('statcan_construction_cost_index.csv','StatCan Construction Cost Index'),
    ('bank_rate_overnight.csv','Bank of Canada Overnight Rate'),
    ('bank_cpi.csv','Bank of Canada CPI series')
]

report = {}

for fn, desc in REQUIRED:
    path = os.path.join(RAW_DIR, fn)
    entry = {'desc': desc, 'present': False, 'readable': False, 'rows': None, 'cols': None, 'error': None}
    if os.path.exists(path):
        entry['present'] = True
        try:
            if fn.lower().endswith('.csv'):
                df = pd.read_csv(path, nrows=5)
                entry['readable'] = True
                entry['rows'] = None
                entry['cols'] = list(df.columns)
            elif fn.lower().endswith(('.geojson','.json')):
                try:
                    import geopandas as gpd
                    gdf = gpd.read_file(path)
                    entry['readable'] = True
                    entry['rows'] = len(gdf)
                    entry['cols'] = list(gdf.columns)
                except Exception as e:
                    entry['error'] = f'Geo parse failed: {e}'
            else:
                entry['error'] = 'Unrecognized extension'
        except Exception as e:
            entry['error'] = str(e)
    else:
        entry['error'] = 'Missing file'
    report[fn] = entry

out_path = os.path.join(RAW_DIR, 'validation_report.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)

print('Validation complete. Report written to', out_path)
print('If any files are missing or unreadable, follow docs/DOWNLOAD_STEPS.md to download them, then re-run this script.')