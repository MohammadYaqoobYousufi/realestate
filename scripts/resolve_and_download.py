"""Resolve and attempt to download datasets with multiple discovery strategies.

For each dataset in DATA_CATALOG, this script will:
 - Check local presence
 - Try direct resource endpoints on data.calgary.ca using provided slug/id
 - Try HTML heuristics on provided URLs
 - Try the catalog API (catalog/v1)
 - Produce a human-readable report in data/raw/download_report.json
"""
import os
import json
import requests
from urllib.parse import urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DIR = os.path.join(ROOT, 'data', 'raw')
os.makedirs(RAW_DIR, exist_ok=True)

TARGETS = [
    {'key':'parcel_addresses', 'title':'Parcel Addresses', 'urls':["https://opendatacalgary.ca/explore/dataset/parcel-addresses" ], 'preferred_name':'parcel_addresses.csv'},
    {'key':'building_permits', 'title':'Building Permits', 'urls':["https://opendatacalgary.ca/explore/dataset/building-permits" ], 'preferred_name':'building_permits.csv'},
    {'key':'development_permits', 'title':'Development Permits', 'urls':["https://opendatacalgary.ca/explore/dataset/development-permits" ], 'preferred_name':'development_permits.csv'},
    {'key':'secondary_suites', 'title':'Calgary Secondary Suites', 'urls':["https://opendatacalgary.ca/explore/dataset/calgary-secondary-suites" ], 'preferred_name':'secondary_suites.csv'},
    {'key':'crime_by_community', 'title':'Crime by Community', 'urls':["https://data.calgary.ca/search?q=crime" ], 'preferred_name':'crime_by_community.csv'},
]

REPORT = {}


def try_direct_resource(slug):
    # Slug might already be a Socrata view id like '4ur7-wsgc'
    candidates = [f'https://data.calgary.ca/resource/{slug}.csv', f'https://data.calgary.ca/resource/{slug}.geojson']
    for url in candidates:
        try:
            r = requests.head(url, timeout=10)
            if r.status_code == 200:
                return url
        except Exception:
            continue
    return None


def html_search_for_download(url):
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200 or not r.text:
            return None
        import re
        m = re.search(r'(https?://[^\"]+(?:resource|download)[^\"]+\.(?:csv|geojson|zip))', r.text, re.IGNORECASE)
        if m:
            return m.group(1)
    except Exception:
        return None
    return None


if __name__ == '__main__':
    print('Resolving datasets with multiple strategies...')
    for t in TARGETS:
        key = t['key']
        REPORT[key] = {'title': t['title'], 'found': False, 'candidates': [], 'notes': []}
        # Already present?
        local_path = os.path.join(RAW_DIR, t['preferred_name'])
        if os.path.exists(local_path):
            REPORT[key]['found'] = True
            REPORT[key]['local_path'] = local_path
            REPORT[key]['notes'].append('Already present locally')
            continue

        # Try direct resource using slug heuristics
        slug_candidate = key.replace('_','-')
        direct = try_direct_resource(slug_candidate)
        if direct:
            REPORT[key]['candidates'].append({'method':'direct_slug_try','url':direct})
            REPORT[key]['notes'].append('Direct resource resolved using slug heuristic')
        # Try HTML discovery
        for u in t.get('urls',[]):
            url = html_search_for_download(u)
            if url:
                REPORT[key]['candidates'].append({'method':'html_discovery','url':url})
                REPORT[key]['notes'].append(f'Found via HTML discovery on {u}')

        # Try catalog/v1 search
        try:
            q = t['title']
            cat_api = f'https://data.calgary.ca/api/catalog/v1?search={q.replace(" ","+")}'
            rc = requests.get(cat_api, timeout=10)
            if rc.status_code == 200:
                js = rc.json()
                if js.get('results'):
                    for it in js['results'][:3]:
                        for res in it.get('resource',[]):
                            url2 = res.get('url')
                            if url2 and any(url2.lower().endswith(ext) for ext in ['.csv','.geojson','.zip']):
                                REPORT[key]['candidates'].append({'method':'catalog_api','url':url2, 'title': it.get('title')})
                                REPORT[key]['notes'].append('Found candidate resource via catalog API')
        except Exception as e:
            REPORT[key]['notes'].append(f'Catalog API error: {e}')

        if not REPORT[key]['candidates']:
            REPORT[key]['notes'].append('No direct candidates found; manual download recommended')

    # Save report
    out_path = os.path.join(RAW_DIR, 'download_report.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(REPORT, f, indent=2)
    print('Report written to', out_path)
    print('Please review the report and either let me try to download candidate URLs or upload the datasets to data/raw/')
