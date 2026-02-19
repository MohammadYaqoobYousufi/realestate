"""Download raw datasets referenced in docs/DATA_CATALOG.md.

This script is cautious: it will attempt to download publicly accessible files and save them to data/raw/.
For Socrata-style datasets (data.calgary.ca), it uses the dataset identifier to request a CSV export.
For zip/shapefiles, it will download and unpack into a subfolder.

NOTE: Some datasets (StatCan, Bank of Canada) may require user interaction or specific endpoints; the script provides clear instructions if automatic download is not possible.
"""
import os
import sys
import requests
import shutil
from urllib.parse import urljoin, urlparse
import zipfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DIR = os.path.join(ROOT, 'data', 'raw')
os.makedirs(RAW_DIR, exist_ok=True)

DATASETS = [

    {
        'name': 'calgary_user_dataset_4ur7-wsgc',
        'url': 'https://data.calgary.ca/resource/4ur7-wsgc.csv',
        'dest': os.path.join(RAW_DIR, '4ur7-wsgc.csv'),
        'note': 'User provided dataset; confirm locally.'
    },
    {
        'name': 'community_boundaries_ab7m-fwn6',
        'url': 'https://data.calgary.ca/resource/ab7m-fwn6.geojson',
        'dest': os.path.join(RAW_DIR, 'community_boundaries.geojson'),
        'note': 'Community boundaries (GeoJSON preferred).'
    },
    {
        'name': 'parcel_addresses',
        'url': 'https://opendatacalgary.ca/explore/dataset/parcel-addresses/download/?format=csv',
        'dest': os.path.join(RAW_DIR, 'parcel_addresses.csv'),
        'note': 'Parcel addresses - CSV.'
    },
    {
        'name': 'building_permits',
        'url': 'https://opendatacalgary.ca/explore/dataset/building-permits/download/?format=csv',
        'dest': os.path.join(RAW_DIR, 'building_permits.csv'),
        'note': 'Building permits.'
    },
    {
        'name': 'development_permits',
        'url': 'https://opendatacalgary.ca/explore/dataset/development-permits/download/?format=csv',
        'dest': os.path.join(RAW_DIR, 'development_permits.csv'),
        'note': 'Development permits.'
    },
    {
        'name': 'secondary_suites',
        'url': 'https://opendatacalgary.ca/explore/dataset/calgary-secondary-suites/download/?format=csv',
        'dest': os.path.join(RAW_DIR, 'secondary_suites.csv'),
        'note': 'Secondary suites dataset.'
    },
    {
        'name': 'crime_by_community',
        'url': 'https://data.calgary.ca/resource/crime.csv',
        'dest': os.path.join(RAW_DIR, 'crime_by_community.csv'),
        'note': 'Crime dataset - may require searching exact dataset id if this fails.'
    },
    {
        'name': 'statcan_construction_cost_index',
        'url': 'https://www150.statcan.gc.ca/n1/tbl/csv/??',
        'dest': os.path.join(RAW_DIR, 'statcan_construction_cost_index.csv'),
        'note': 'Statistics Canada construction price index (manual or API-based download).'
    },
    {
        'name': 'statcan_census_ct_or_da',
        'url': 'MANUAL: Download Census Profile (CT/DA) CSV from Statistics Canada for Calgary',
        'dest': os.path.join(RAW_DIR, 'statcan_census_ct_da.csv'),
        'note': 'StatsCan census profiles require manual selection or scripted API access. See docs.'
    },
    {
        'name': 'bank_of_canada_rates',
        'url': 'https://www.bankofcanada.ca/valet/observations/FXACAD/csv',
        'dest': os.path.join(RAW_DIR, 'bank_of_canada_rates.csv'),
        'note': 'Example: Exchange rates or use Valet API for interest rates/inflation series.'
    }
]


def download_url(url, dest, stream=True, retries=2):
    print(f"Downloading {url} -> {dest}")
    try:
        with requests.get(url, stream=stream, timeout=30) as r:
            if r.status_code >= 400:
                print(f"  Failed to download: HTTP {r.status_code} {r.reason}")
                return False
            with open(dest, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        return True
    except Exception as e:
        print(f"  Exception: {e}")
        return False


def safe_write_note(note, dest):
    # sidecar file with notes about original URL & license
    meta_path = dest + '.metadata.txt'
    with open(meta_path, 'w', encoding='utf-8') as f:
        f.write(note + '\n')


if __name__ == '__main__':
    print('Running dataset downloader. Ensure you have network access. Some datasets may require manual download due to portal constraints.')
    for ds in DATASETS:
        url = ds['url']
        dest = ds['dest']
        note = f"Source: {ds.get('url')}\nNote: {ds.get('note')}"

        if url.startswith('MANUAL:'):
            print(f" - {ds['name']}: MANUAL step required. See docs/DATA_CATALOG.md -> {ds['note']}")
            safe_write_note(note, dest)
            continue

        # If the URL looks like an 'explore/dataset' page (opendatacalgary), try to resolve a direct CSV/GeoJSON endpoint
        if '/explore/dataset/' in url or 'opendatacalgary' in url:
            resolved = None
            try:
                print(f"  Resolving dataset page {url} for direct download links via HTML heuristics...")
                r = requests.get(url, timeout=15)
                if r.status_code == 200 and r.text:
                    # Look for download endpoints in page HTML
                    import re
                    m = re.search(r'(https?://[^\"]+(?:resource|download)[^\"]+\.(?:csv|geojson|zip))', r.text, re.IGNORECASE)
                    if m:
                        resolved = m.group(1)
                # If not found, try Socrata/OpenData catalog search API for dataset by name
                if not resolved:
                    print("  HTML heuristic failed; trying the City catalog API to locate resources...")
                    # Extract a candidate search term from the explore URL
                    try:
                        # e.g. https://opendatacalgary.ca/explore/dataset/parcel-addresses
                        parts = url.split('/')
                        idx = parts.index('dataset') if 'dataset' in parts else -1
                        term = parts[idx+1] if idx != -1 and len(parts) > idx+1 else parts[-1]
                    except Exception:
                        term = url
                    catalog_api = f'https://data.calgary.ca/api/catalog/v1?search={term}'
                    cr = requests.get(catalog_api, timeout=15)
                    if cr.status_code == 200 and cr.json():
                        items = cr.json().get('results', [])
                        # pick the top result that has resources
                        for it in items:
                            resources = it.get('resource', [])
                            if resources:
                                # find a resource with csv/geojson/zip
                                for res in resources:
                                    url2 = res.get('url')
                                    if url2 and any(url2.lower().endswith(ext) for ext in ['.csv', '.geojson', '.zip']):
                                        resolved = url2
                                        break
                            if resolved:
                                break
                if resolved:
                    print(f"  Found candidate download URL: {resolved}")
                    ok = download_url(resolved, dest)
                else:
                    print(f"  Could not find direct download link on the explore page or catalog API. Please download manually and save to {dest}")
                    ok = False
            except Exception as e:
                print(f"  Exception while resolving explore page/catalog API: {e}")
                ok = False
        else:
            ok = download_url(url, dest)

        if not ok:
            print(f"  Automatic download failed for {ds['name']}. You may need to manually download the dataset and save to: {dest}")
            safe_write_note(note, dest)
        else:
            safe_write_note(note, dest)
            print(f"  Saved to {dest}")

    print('\nDataset download attempt complete. Please check data/raw/ and consult docs/DATA_CATALOG.md for manual steps.')
