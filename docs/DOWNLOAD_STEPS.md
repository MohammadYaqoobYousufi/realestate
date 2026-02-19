# Manual Download Steps — City of Calgary & National Series

Some datasets could not be downloaded automatically due to portal page structures or dynamic download links. Follow these steps to download the missing datasets and place them in `data/raw/` using the exact filenames below so the ingestion scripts can pick them up automatically.

Required files and exact target filenames

1) Parcel Addresses (CSV)
- Portal page: https://opendatacalgary.ca/explore/dataset/parcel-addresses
- Save as: `data/raw/parcel_addresses.csv`
- Purpose: canonical parcel geometry and addresses for validation and join keys.

2) Building Permits (CSV)
- Portal page: https://opendatacalgary.ca/explore/dataset/building-permits
- Save as: `data/raw/building_permits.csv`
- Purpose: supply signals (new builds, major renovations).

3) Development Permits (CSV)
- Portal page: https://opendatacalgary.ca/explore/dataset/development-permits
- Save as: `data/raw/development_permits.csv`
- Purpose: zoning/land-use approvals and planned supply.

4) Calgary Secondary Suites (CSV)
- Portal page: https://opendatacalgary.ca/explore/dataset/calgary-secondary-suites
- Save as: `data/raw/secondary_suites.csv`
- Purpose: rental unit inventory and ADU signals.

5) Crime by Community (CSV)
- City portal search: https://data.calgary.ca/ (search "Crime by Community")
- Save as: `data/raw/crime_by_community.csv`
- Purpose: neighborhood safety signals.

6) Statistics Canada — Census Profiles (CT/DA)
- Open StatsCan portal: https://www12.statcan.gc.ca/census-recensement/index-eng.cfm
- Download CT or DA profile CSV for Calgary (choose the geography you prefer) and save as:
  - `data/raw/statcan_census_ct_da.csv` (or similar consistent name)
- Purpose: socio-economic demand signals (income, household size, tenure, population).

7) StatCan — Residential Construction Price Index or Construction Cost Index
- Portal: https://www.statcan.gc.ca/eng/subjects-start/construction
- Save as: `data/raw/statcan_construction_cost_index.csv`
- Purpose: replacement cost and inflation adjustments.

8) Bank of Canada series (macro)
- Use Bank of Canada Valet API or their download page. Recommended series for the platform:
  - Overnight Rate (policy rate) → save as: `data/raw/bank_rate_overnight.csv`
  - Consumer Price Index (CPI) series → save as: `data/raw/bank_cpi.csv`
- You can fetch these via the Valet API (e.g., https://www.bankofcanada.ca/valet/observations/<SERIES_ID>/csv) where `<SERIES_ID>` is the timeseries code. If unsure, download CSV from the web UI and place them in `data/raw/`.

Notes & tips
- If a dataset is available as a zipped shapefile, extract the shapefile and either save as GeoJSON (`.geojson`) or as the original shapefile files under a directory `data/raw/<datasetname>/`.
- Keep original license/provenance files — save attachments and license text alongside the raw data files.
- Filenames must match those above (case-insensitive) so the `scripts/prepare_datasets.py` picks them up.

After downloads — run these commands

1. Activate the venv:
   - Windows PowerShell: `envs\Scripts\Activate.ps1`
2. Validate raw files and run preparation (automated):
   - `python scripts/validate_raw_files.py`  (this checks presence + minimal schema checks)
   - `python scripts/prepare_datasets.py`  (creates samples and `data/processed/manifest.json`)

If you want, upload the files (or give me direct download URLs) and I will run the validation and preparation for you.

---

## Automated option: Playwright headless fetch (advanced) ⚙️

If you'd prefer the agent to try extracting dynamic download links automatically, use Playwright. This runs a headless browser to execute page JavaScript and capture export/download URLs.

Quick steps:

1. Activate the venv: `envs\Scripts\Activate.ps1`
2. Install Playwright and browsers: `scripts\setup_playwright.ps1`
3. Run the automated fetcher: `python scripts/playwright_fetch.py`

Outputs:
- `data/raw/playwright_report.json` contains discovered candidate URLs and per-file download status.
- Any successful downloads are saved into `data/raw/`.

Notes:
- Playwright is powerful but not guaranteed: some portals require interactive filtering or server-side checks that still need manual intervention.
- Review `data/raw/playwright_report.json` and the downloaded files; if key datasets are missing, please follow the Manual Download Steps above.

