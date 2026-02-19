import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd
import os
import time
import json

# Role: The "Collector". Handles all downloads (Socrata, BoC, Census) with retry logic and state saving.
# --- CONFIGURATION ---
DATA_DIR = r"D:\realestate\data\raw"
STATE_DIR = r"D:\realestate\data\states"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)

# Central Registry of All Data Sources
CATALOG = {
    # Core Real Estate Data
    "current_assessments": {"id": "4bsw-nn7w", "type": "socrata"},
    "historical_assessments": {"id": "4ur7-wsgc", "type": "socrata"},
    
    # Context Layers (Supply & Crime)
    "building_permits": {"id": "c2es-76ed", "type": "socrata"},
    "development_permits": {"id": "6936-8n7m", "type": "socrata"}, # Updated ID
    "secondary_suites": {"id": "g5zp-wv9h", "type": "socrata"},
    "community_crime": {"id": "78gh-n26t", "type": "socrata"},
    "community_census": {"id": "rk77-87m6", "type": "socrata"},
    
    # Macro Economics
    "macro_rates": {
        "url": "https://www.bankofcanada.ca/valet/observations/V80691311/json", 
        "type": "boc"
    }
}

def get_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def download_socrata(name, dataset_id):
    csv_path = os.path.join(DATA_DIR, f"{name}.csv")
    state_path = os.path.join(STATE_DIR, f"{name}_state.json")
    offset = 0
    
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            offset = json.load(f).get('offset', 0)

    print(f"🚀 [SOCRATA] Fetching {name} (ID: {dataset_id}) from row {offset:,}...")
    session = get_session()
    chunk_size = 50000 

    while True:
        try:
            url = f"https://data.calgary.ca/resource/{dataset_id}.json?$limit={chunk_size}&$offset={offset}&$order=:id"
            r = session.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()

            if not data:
                print(f"✅ {name.upper()} Download Complete.")
                if os.path.exists(state_path): os.remove(state_path)
                break

            df = pd.DataFrame(data)
            # Write header only on first chunk of new file
            header = True if offset == 0 else False
            mode = 'w' if offset == 0 else 'a'
            
            df.to_csv(csv_path, mode=mode, index=False, header=header)
            
            offset += len(data)
            with open(state_path, 'w') as f: json.dump({'offset': offset}, f)
            print(f"📦 Saved {offset:,} rows...", end='\r')

        except Exception as e:
            print(f"\n⚠️ Error at {offset}: {e}. Retrying in 10s...")
            time.sleep(10)

def download_boc():
    print("\n🚀 [BoC] Fetching Interest Rates...")
    dest = os.path.join(DATA_DIR, "interest_rates.json")
    try:
        r = requests.get(CATALOG["macro_rates"]["url"])
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)
        print("✅ Macro data secured.")
    except Exception as e:
        print(f"❌ BoC Download Failed: {e}")

if __name__ == "__main__":
    print("--- 📡 DATA ACQUISITION ENGINE STARTING ---")
    
    # 1. Download Macro Data
    download_boc()
    
    # 2. Download Socrata Datasets
    for name, info in CATALOG.items():
        if info["type"] == "socrata":
            download_socrata(name, info["id"])
            
    print("\n🏁 ALL DOWNLOADS COMPLETE.")