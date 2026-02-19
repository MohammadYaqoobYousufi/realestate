# Data Catalog & Preparation Plan

This document lists the raw datasets required for the Agentic AI real-estate intelligence platform and provides a concrete, reproducible plan to download, validate, and stage them locally under `data/raw/` and `data/processed/`.

Purpose
- Ensure the repo contains all necessary, local-only datasets for price modeling, CMA, AVM, forecasting, risk analyses, fraud detection, and geospatial analysis.
- Provide a reproducible script-based way to fetch, validate, and prepare datasets.

Datasets (priority order)

1) User-provided dataset (already downloaded)
- URL: https://data.calgary.ca/d/4ur7-wsgc
- Local path expected: `data/raw/4ur7-wsgc.*` (CSV / GeoJSON / zip)
- Notes: User already downloaded. Confirm schema and mapping to property records.
- Importance: HIGH — likely core transaction/assessment data (confirm locally).

2) Community Boundaries (Spatial Features)
- URL: https://data.calgary.ca/d/ab7m-fwn6
- Format: Shapefile / GeoJSON (zipped shapefile likely)
- Local path: `data/raw/community_boundaries/*`
- Importance: HIGH — used for aggregating market signals, neighborhood features, and geospatial joins.

3) Parcel Addresses (Spatial / Validation)
- URL: https://opendatacalgary.ca/explore/dataset/parcel-addresses
- Format: CSV / GeoJSON
- Local path: `data/raw/parcel_addresses.*`
- Importance: HIGH — canonical spatial keys for properties and address validation.

4) Building Permits (Supply Signals)
- URL: https://opendatacalgary.ca/explore/dataset/building-permits
- Format: CSV
- Local path: `data/raw/building_permits.csv`
- Importance: HIGH — construction activity, supply shocks, new builds, renovations.

5) Development Permits (Zoning / Land Use)
- URL: https://opendatacalgary.ca/explore/dataset/development-permits
- Format: CSV
- Local path: `data/raw/development_permits.csv`
- Importance: MEDIUM-HIGH — land use changes and zoning shifts that influence price and risk.

6) Secondary Suites (Rental / Additional Value)
- URL: https://opendatacalgary.ca/explore/dataset/calgary-secondary-suites
- Format: CSV
- Local path: `data/raw/secondary_suites.csv`
- Importance: MEDIUM — informs rental capacity and income potential for investment scoring.

7) Socio-Economic & Census Data (Demand Signals)
- URL: https://www12.statcan.gc.ca/census-recensement/index-eng.cfm
- Granularity: Census Tract (CT) or Dissemination Area (DA)
- Local path: `data/raw/statcan_census_*` (CSV)
- Importance: HIGH — demographic controls, income, family structure, unemployment, etc.
- Note: We'll provide a helper that instructs how to download DA/CT-level profiles for Calgary and a script to attach them to neighborhoods.

8) Crime Data (Safety Signals)
- Source: City of Calgary Open Data — search for “Crime by Community” (CSV/XLS)
- Local path: `data/raw/crime_by_community.csv`
- Importance: MEDIUM — safety impacts market desirability and rental demand.

9) Construction Cost Index (Replacement Cost)
- Source: Statistics Canada — residential construction cost index
- URL: https://www.statcan.gc.ca/eng/subjects-start/construction
- Local path: `data/raw/canada_construction_cost_index.csv`
- Importance: MEDIUM — for replacement cost estimations and insurance/risk modeling.

10) Macro / Market Context (Temporal Adjustment)
- Source: Bank of Canada (interest rates, inflation, affordability series)
- URL: https://www.bankofcanada.ca/rates/related-statistics/
- Local path: `data/raw/bankofcanada_rates.csv`
- Importance: HIGH — adjust forecasts, discount rates, affordability analyses.

Licensing & Provenance
- Each dataset entry should contain license information. Verify license and store a `LICENSE` or `README` with the raw file.
- For datasets with usage restrictions, document and avoid redistribution in derivative distributions.

Quality checks and staging
- A pair of scripts are added:
  - `scripts/download_datasets.py` — attempts to download datasets automatically; falls back to instructions if manual download is required.
  - `scripts/prepare_datasets.py` — validates file formats, converts shapefiles to GeoJSON, sanity-checks columns, samples rows, and writes cleaned files to `data/processed/`.
- Validation steps include: schema checks, coordinate reference system normalization (to EPSG:4326), deduplication, basic type casting, and recording provenance in `data/catalog.json`.

Next steps
- Run `python scripts/download_datasets.py` after ensuring network access and accepting any licensing terms for models/data.
- Run `python scripts/prepare_datasets.py` to generate `data/processed/*` artifacts and a manifest with column mappings.

Contact
- If you want, I can run quick local schema discovery for the dataset you already downloaded (provide the path to the file), and then continue automatic ingestion for the rest. Provide the paths or allow me to proceed with downloads.
