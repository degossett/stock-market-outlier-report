import os
import json
import time
import threading
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TAXONOMY_JSON = os.path.join(BASE_DIR, "master_taxonomy_hierarchical.json")
OVERVIEWS_JSON = os.path.join(BASE_DIR, "qwen_visual_overviews.json")
OUTPUT_JSON = os.path.join(BASE_DIR, "deepseek_material_movers.json")

# Initialize Direct DeepSeek Client
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Using DeepSeek V4 (deepseek-chat)
MODEL_NAME = "deepseek-chat"
MAX_WORKERS = 5
file_lock = threading.Lock()

def build_flat_metadata(taxonomy_data):
    """Flattens the hierarchical taxonomy so we can easily look up any ticker."""
    flat_data = {}
    for category, sectors in taxonomy_data.items():
        for sector, companies in sectors.items():
            for ticker, data in companies.items():
                flat_data[ticker] = {
                    "company_name": data.get("company_name", "Unknown"),
                    "market_cap": data.get("market_cap", 0),
                    "category": category,
                    "sector": sector
                }
    return flat_data

def evaluate_materiality(ticker, metadata, overview):
    """Sends the text payload to DeepSeek to determine if the stock is a material anomaly."""
    
    prompt = f"""
You are an elite quantitative equity analyst. Your task is to evaluate a single U.S. equity to determine if its price action today represents a Material Idiosyncratic Anomaly or simply boring, in-pattern market noise.

**Company Profile:**
* Ticker: {ticker}
* Company: {metadata['company_name']}
* Market Cap: ${metadata['market_cap']:,.0f}
* Sector / Sub-Sector: {metadata['category']} / {metadata['sector']}

**Visual Field Report (from Vision AI):**
"{overview}"

**Instructions:**
Rely strictly on your inherent training regarding equity markets, volatility, and market cap scale. Does this stock's visual price action and fundamental profile indicate a massive, market-moving anomaly (e.g., a massive gap-and-hold, a severe structural breakdown), or is this just standard, boring intraday noise?

If it is BORING, return ONLY the exact word: NOISE
If it is MATERIAL, return a single, highly professional 4-sentence paragraph explaining exactly why this move is highly unusual and newsletter-worthy. Do not include introductory or conversational text.
"""
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"      [!] API Error on {ticker}: {e}")
        return None

def process_single_stock(ticker, metadata, overview, results):
    """Worker function to process one stock and thread-safely save."""
    max_retries = 3
    
    for attempt in range(max_retries):
        analysis = evaluate_materiality(ticker, metadata, overview)
        if analysis:
            break
            
        sleep_time = 2 ** attempt
        time.sleep(sleep_time)
        
    if analysis:
        with file_lock:
            # We only save it if it's material; we throw away the "NOISE"
            if analysis.upper() != "NOISE":
                results[ticker] = analysis
            else:
                # Store a placeholder so we know it was processed and rejected
                results[ticker] = "NOISE"
                
            with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4)
        return ticker, True
        
    return ticker, False

def run_materiality_filter():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 10.0: The Materiality Filter (DeepSeek V4)...")
    
    if not os.path.exists(OVERVIEWS_JSON) or not os.path.exists(TAXONOMY_JSON):
        print("⚠️ Required JSON files missing. Make sure Scripts 06 and 09 have run.")
        return
        
    with open(TAXONOMY_JSON, 'r', encoding='utf-8') as f:
        taxonomy_data = json.load(f)
    flat_metadata = build_flat_metadata(taxonomy_data)
    
    with open(OVERVIEWS_JSON, 'r', encoding='utf-8') as f:
        overviews_data = json.load(f)
        
    results = {}
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
            results = json.load(f)
            print(f">>> Found {len(results)} existing evaluations. Resuming...")
            
    unprocessed_tickers = [t for t in overviews_data.keys() if t not in results]
    
    if not unprocessed_tickers:
        print(">>> All stocks have been evaluated by DeepSeek! Exiting.")
        return
        
    print(f">>> Evaluating {len(unprocessed_tickers)} stocks using {MAX_WORKERS} concurrent workers...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_ticker = {
            executor.submit(
                process_single_stock, 
                ticker, 
                flat_metadata.get(ticker, {"company_name": "Unknown", "market_cap": 0, "category": "Unknown", "sector": "Unknown"}), 
                overviews_data[ticker], 
                results
            ): ticker 
            for ticker in unprocessed_tickers
        }
        
        completed = 0
        material_count = 0
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                _, success = future.result()
                completed += 1
                
                # Check if it was flagged as material or noise
                if success and results.get(ticker) != "NOISE":
                    status = "🔥 MATERIAL"
                    material_count += 1
                elif success:
                    status = "💤 NOISE"
                else:
                    status = "❌ ERROR"
                    
                print(f"  ... [{completed}/{len(unprocessed_tickers)}] {status} | {ticker}")
            except Exception as exc:
                print(f"  ❌ {ticker} generated an exception: {exc}")
                
    print(f"\n✅ Success! DeepSeek identified {material_count} material anomalies.")
    print(f"Results saved to: {OUTPUT_JSON}")

if __name__ == '__main__':
    run_materiality_filter()