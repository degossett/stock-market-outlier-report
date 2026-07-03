import os
import json
import time
from datetime import datetime
import yfinance as yf

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ISHARES_JSON = os.path.join(BASE_DIR, "ishares_base_list.json")
YAHOO_JSON = os.path.join(BASE_DIR, "yahoo_metadata.json") # Totally separate file!

def run_yahoo_enrichment():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 03.0: Yahoo Data Pull...")
    
    if not os.path.exists(ISHARES_JSON):
        print(f"⚠️ Base list not found. Run 02.0_parse_ishares.py first.")
        return

    # Load the base list strictly to get the target ticker symbols
    with open(ISHARES_JSON, 'r', encoding='utf-8') as f:
        base_data = json.load(f)
        all_tickers = list(base_data.keys())
        
    # Load existing Yahoo metadata if it exists (for resuming)
    yahoo_metadata = {}
    if os.path.exists(YAHOO_JSON):
        with open(YAHOO_JSON, 'r', encoding='utf-8') as f:
            yahoo_metadata = json.load(f)
            print(f">>> Found existing Yahoo data with {len(yahoo_metadata)} records. Resuming...")

    # Figure out which tickers we still need to process
    tickers_to_process = [t for t in all_tickers if t not in yahoo_metadata]
    
    if not tickers_to_process:
        print(">>> All tickers have already been pulled from Yahoo! Exiting.")
        return

    # --- TESTING MODE ---
    # Uncomment the two lines below if you want to test just the first 10 before running all 2500+
    # tickers_to_process = tickers_to_process[:10] 
    # print(f">>> PROCESSING {len(tickers_to_process)} MISSING TICKERS (Testing Mode Active)...")
    
    print(f">>> Fetching Yahoo data for {len(tickers_to_process)} tickers...")

    for i, ticker in enumerate(tickers_to_process):
        try:
            info = yf.Ticker(ticker).info
            yahoo_metadata[ticker] = {
                "yahoo_sector": info.get('sector', 'Unknown'),
                "yahoo_industry": info.get('industry', 'Unknown'),
                "market_cap": info.get('marketCap', 0),
                "total_revenue": info.get('totalRevenue', 0),
                "long_description": info.get('longBusinessSummary', 'No description available.')
            }
            print(f"  [+] Fetched {ticker}")
            
            # Save the file after every single ticker. 
            # If the script crashes, you lose zero progress!
            with open(YAHOO_JSON, 'w', encoding='utf-8') as f:
                json.dump(yahoo_metadata, f, indent=4)
                
        except Exception as e:
            print(f"  [!] Failed to fetch {ticker}: {e}")
            # Mark it as an error in the JSON so it doesn't get stuck in an infinite retry loop
            yahoo_metadata[ticker] = {
                "yahoo_sector": "Error",
                "yahoo_industry": "Error",
                "market_cap": 0,
                "total_revenue": 0,
                "long_description": "Failed to fetch from Yahoo."
            }
            with open(YAHOO_JSON, 'w', encoding='utf-8') as f:
                json.dump(yahoo_metadata, f, indent=4)
            continue
            
        if (i + 1) % 50 == 0:
            print(f"  ... Pausing for 2 seconds to respect Yahoo's rate limits.")
            time.sleep(2)

    print(f"\n✅ Success! Yahoo metadata saved to: {YAHOO_JSON}")

if __name__ == '__main__':
    run_yahoo_enrichment()