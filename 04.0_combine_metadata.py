import os
import json
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Input Files
ISHARES_JSON = os.path.join(BASE_DIR, "ishares_base_list.json")
YAHOO_JSON = os.path.join(BASE_DIR, "yahoo_metadata.json")
DEEPSEEK_JSON = os.path.join(BASE_DIR, "deepseek_taxonomy.json")

# Output File
COMBINED_JSON = os.path.join(BASE_DIR, "master_taxonomy_combined.json")

def combine_metadata():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 05.0: Combining Metadata...")

    # 1. Load all three JSON files
    try:
        with open(ISHARES_JSON, 'r', encoding='utf-8') as f:
            ishares_data = json.load(f)
        print(f">>> Loaded {len(ishares_data)} records from iShares.")
        
        with open(YAHOO_JSON, 'r', encoding='utf-8') as f:
            yahoo_data = json.load(f)
        print(f">>> Loaded {len(yahoo_data)} records from Yahoo.")
        
        with open(DEEPSEEK_JSON, 'r', encoding='utf-8') as f:
            deepseek_data = json.load(f)
        print(f">>> Loaded {len(deepseek_data)} records from DeepSeek.")
            
    except Exception as e:
        print(f"⚠️ Error loading source JSON files: {e}")
        return

    # 2. Build the Combined Dictionary
    master_combined = {}
    
    print(">>> Merging targeted fields (dropping long_description)...")
    
    # We use iShares as the anchor since it represents the true Russell 3000 list
    for ticker, ishares_info in ishares_data.items():
        
        # Safely grab the corresponding data from the other files (default to empty dict if missing)
        y_info = yahoo_data.get(ticker, {})
        ds_info = deepseek_data.get(ticker, {})
        
        master_combined[ticker] = {
            # From iShares
            "company_name": ishares_info.get("company_name", "Unknown"),
            "ishares_sector": ishares_info.get("ishares_sector", "Unknown"),
            
            # From Yahoo (Excluding long_description)
            "yahoo_sector": y_info.get("yahoo_sector", "Unknown"),
            "yahoo_industry": y_info.get("yahoo_industry", "Unknown"),
            "market_cap": y_info.get("market_cap", 0),
            "total_revenue": y_info.get("total_revenue", 0),
            
            # From DeepSeek
            "deepseek_subsector": ds_info.get("deepseek_subsector", "Unclassified"),
            "deepseek_rationale": ds_info.get("deepseek_rationale", "No rationale provided.")
        }

    # 3. Save the final combined JSON
    print(f"\n>>> Saving {len(master_combined)} cleaned records to JSON...")
    try:
        with open(COMBINED_JSON, 'w', encoding='utf-8') as f:
            json.dump(master_combined, f, indent=4)
        print(f"✅ Success! Combined master taxonomy locked in at: {COMBINED_JSON}")
    except Exception as e:
        print(f"⚠️ Error saving combined JSON: {e}")

if __name__ == '__main__':
    combine_metadata()