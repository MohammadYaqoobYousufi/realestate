"""Playwright-based fetcher for dynamic portal pages.

Usage:
  - Ensure Playwright is installed and browsers are installed (see scripts/setup_playwright.ps1)
  - Run: `python scripts/playwright_fetch.py`

What it does:
  - Visits each target page headlessly
  - Captures any network responses or hrefs that look like CSV/GEOJSON/ZIP
  - Attempts to download discovered resources into data/raw/ with sensible filenames
  - Writes `data/raw/playwright_report.json` with candidates and download status
"""
import os
import json
import re
import time
import requests
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DIR = os.path.join(ROOT, 'data', 'raw')
os.makedirs(RAW_DIR, exist_ok=True)

TARGETS = {
    'parcel_addresses': 'https://opendatacalgary.ca/explore/dataset/parcel-addresses',
    'building_permits': 'https://opendatacalgary.ca/explore/dataset/building-permits',
    'development_permits': 'https://opendatacalgary.ca/explore/dataset/development-permits',
    'secondary_suites': 'https://opendatacalgary.ca/explore/dataset/calgary-secondary-suites',
    'crime_by_community': 'https://data.calgary.ca/search?q=crime'
}

RESOURCE_RE = re.compile(r'https?://[^\"\'"\s]+\.(?:csv|geojson|zip)(?:\?[^\"\'"\s]*)?', re.IGNORECASE)

report = {}


def download_url_to(path, url):
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True, None
    except Exception as e:
        return False, str(e)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for key, url in TARGETS.items():
        print('Visiting', url)
        context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        page = context.new_page()

        found = set()
        downloads = []

        # Intercept network responses
        def handle_response(response):
            try:
                rurl = response.url
                if RESOURCE_RE.search(rurl):
                    found.add(rurl)
            except Exception:
                pass

        page.on('response', handle_response)

        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(1)

            # Search page for static links
            html = page.content()
            for m in RESOURCE_RE.finditer(html):
                found.add(m.group(0))

            # Look for obvious export buttons and click them to trigger downloads
            for sel_text in ['Export', 'Download', 'CSV', 'GeoJSON', 'KML']:
                try:
                    loc = page.locator(f'text="{sel_text}"')
                    count = loc.count()
                    for i in range(count):
                        try:
                            el = loc.nth(i)
                            el.click(timeout=3000)
                            time.sleep(0.5)
                        except Exception:
                            pass
                except Exception:
                    pass

            # check for links with download attributes
            try:
                anchors = page.query_selector_all('a')
                for a in anchors:
                    href = a.get_attribute('href')
                    if href and RESOURCE_RE.search(href):
                        # normalize to absolute
                        if href.startswith('http'):
                            found.add(href)
                        else:
                            found.add(page.url.rstrip('/') + '/' + href.lstrip('/'))
            except Exception:
                pass

            report[key] = {'page': url, 'candidates': [], 'downloaded': []}
            for f in sorted(found):
                fname = os.path.basename(f.split('?')[0])
                target_path = os.path.join(RAW_DIR, fname)
                ok, err = download_url_to(target_path, f)
                report[key]['candidates'].append({'url': f, 'filename': fname, 'downloaded': ok, 'error': err})
                if ok:
                    report[key]['downloaded'].append(target_path)

            # Close context
            context.close()
        except Exception as e:
            report[key] = {'page': url, 'error': str(e), 'candidates': [], 'downloaded': []}
            try:
                context.close()
            except Exception:
                pass

    with open(os.path.join(RAW_DIR, 'playwright_report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print('Playwright fetch complete. Report written to data/raw/playwright_report.json')
    browser.close()