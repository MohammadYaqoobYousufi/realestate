"""Aggressive fetch for dataset download links using browser-like headers and multiple heuristics.

This script targets the missing Calgary datasets and attempts to discover direct CSV/GeoJSON/ZIP URLs by:
 - fetching pages with a common browser User-Agent
 - searching HTML for known patterns (resource, api/views, download, .csv, .geojson, .zip)
 - inspecting inline JSON (Socrata/ArcGIS snippets)

It writes a report to data/raw/aggressive_report.json with any candidate URLs found.
"""
import os
import json
import requests
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DIR = os.path.join(ROOT, 'data', 'raw')
os.makedirs(RAW_DIR, exist_ok=True)

TARGET_URLS = {
    'parcel_addresses': 'https://opendatacalgary.ca/explore/dataset/parcel-addresses',
    'building_permits': 'https://opendatacalgary.ca/explore/dataset/building-permits',
    'development_permits': 'https://opendatacalgary.ca/explore/dataset/development-permits',
    'secondary_suites': 'https://opendatacalgary.ca/explore/dataset/calgary-secondary-suites',
    'crime_by_community': 'https://data.calgary.ca/search?q=crime'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
}

REPORT = {}

URL_PATTERN = re.compile(r'https?://[^\"\']+\.(?:csv|geojson|zip)(?:\?[^\"\']*)?', re.IGNORECASE)
RESOURCE_PATTERN = re.compile(r'https?://[^\"\']+/(?:resource|api|download)[^\"\']*', re.IGNORECASE)


def find_candidates(text):
    candidates = set()
    for m in URL_PATTERN.finditer(text):
        candidates.add(m.group(0))
    # find resource-like urls
    for m in RESOURCE_PATTERN.finditer(text):
        candidates.add(m.group(0))
    return list(candidates)


if __name__ == '__main__':
    for key, url in TARGET_URLS.items():
        print('Fetching', url)
        REPORT[key] = {'page': url, 'candidates': [], 'notes': []}
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and r.text:
                text = r.text
                # run candidate extraction
                cands = find_candidates(text)
                REPORT[key]['candidates'] = cands
                REPORT[key]['notes'].append(f'Found {len(cands)} candidate links via regex')

                # Look for JSON embedded in scripts (Socrata/ArcGIS snippets)
                for script in re.findall(r'<script[^>]*>(.*?)</script>', text, re.DOTALL | re.IGNORECASE):
                    # search for urls inside
                    c2 = find_candidates(script)
                    for u in c2:
                        if u not in cands:
                            cands.append(u)
                REPORT[key]['candidates'] = cands

                # Heuristic: check for data.calgary.ca api endpoints by constructing search queries
                # also try to detect dataset id patterns like /d/<id>
                mid = re.search(r'/d/([a-z0-9\-]{6,})', url, re.IGNORECASE)
                if mid:
                    possible_id = mid.group(1)
                    REPORT[key]['notes'].append(f'Detected portal id {possible_id}; testing resource endpoints')
                    possible_urls = [
                        f'https://data.calgary.ca/resource/{possible_id}.csv',
                        f'https://data.calgary.ca/resource/{possible_id}.geojson'
                    ]
                    for pu in possible_urls:
                        try:
                            rr = requests.head(pu, headers=HEADERS, timeout=8, allow_redirects=True)
                            if rr.status_code == 200:
                                cands.append(pu)
                                REPORT[key]['notes'].append(f'resource endpoint ok: {pu}')
                        except Exception:
                            pass
                # Deduplicate
                REPORT[key]['candidates'] = sorted(list(dict.fromkeys(REPORT[key]['candidates'])))
            else:
                REPORT[key]['notes'].append(f'HTTP {r.status_code}')
        except Exception as e:
            REPORT[key]['notes'].append(str(e))

    out = os.path.join(RAW_DIR, 'aggressive_report.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(REPORT, f, indent=2)
    print('Aggressive report written to', out)
    for k, v in REPORT.items():
        print('-', k, 'candidates:', len(v.get('candidates', [])))
