import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load API keys from your .env file
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") 

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YAHOO_JSON = os.path.join(BASE_DIR, "yahoo_metadata.json")
DEEPSEEK_JSON = os.path.join(BASE_DIR, "deepseek_taxonomy.json")

def get_deepseek_taxonomy(chunk_data):
    """Sends a chunk of companies to DeepSeek to generate modern subsectors."""
    # We use the standard OpenAI client, but point it to DeepSeek's servers
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com") 
    
    prompt = f"""
    You are an expert quantitative financial analyst. 
    Below is a JSON object containing a list of stock tickers, their legacy sectors, and their business descriptions.
    
    For each company, please:
    1. Assign it to a highly specific "Modern Macro-Sector" (e.g., 'AI Infrastructure', 'Regional Banking', 'Biotech R&D', 'Cloud Cybersecurity'). Do not just use generic terms like "Technology".
    2. Write a single, concise sentence explaining exactly what the company does to justify this sector.
    
    RETURN ONLY VALID JSON in this exact format:
    {{
        "TICKER": {{
            "deepseek_subsector": "Modern Sector Name",
            "deepseek_rationale": "One sentence explanation."
        }}
    }}
    
    Companies to analyze:
    {json.dumps(chunk_data, indent=2)}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # This routes to their latest V4/frontier model
            messages=[
                {"role": "system", "content": "You are a data formatting assistant that only outputs raw JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        raw_output = response.choices[0].message.content
        # Clean markdown wrappers if the LLM includes them
        clean_json = raw_output.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"❌ API Error: {e}")
        return {}

def run_taxonomy_enrichment():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 04.0: DeepSeek Taxonomy Enrichment...")
    
    if not os.path.exists(YAHOO_JSON):
        print("⚠️ Yahoo metadata JSON not found. Please wait for Step 03 to finish.")
        return
        
    with open(YAHOO_JSON, 'r', encoding='utf-8') as f:
        yahoo_metadata = json.load(f)
        
    # Load existing DeepSeek taxonomies if they exist (for resuming)
    deepseek_data = {}
    if os.path.exists(DEEPSEEK_JSON):
        with open(DEEPSEEK_JSON, 'r', encoding='utf-8') as f:
            deepseek_data = json.load(f)
            print(f">>> Found existing DeepSeek data with {len(deepseek_data)} records. Resuming...")

    # Isolate tickers that haven't been processed by DeepSeek yet
    unprocessed_tickers = [t for t in yahoo_metadata.keys() if t not in deepseek_data]
    
    if not unprocessed_tickers:
        print(">>> All tickers have already been categorized by DeepSeek! Exiting.")
        return
        
    print(f">>> Found {len(unprocessed_tickers)} companies needing DeepSeek analysis.")
    
    chunk_size = 50 # Safe chunk size to avoid hitting output token limits
    
    for i in range(0, len(unprocessed_tickers), chunk_size):
        chunk_tickers = unprocessed_tickers[i:i+chunk_size]
        
        # Build a lightweight payload for the LLM to save input tokens and costs
        chunk_payload = {}
        for t in chunk_tickers:
            chunk_payload[t] = {
                "yahoo_sector": yahoo_metadata[t].get("yahoo_sector"),
                "yahoo_industry": yahoo_metadata[t].get("yahoo_industry"),
                "long_description": yahoo_metadata[t].get("long_description")
            }
        
        print(f"  ... Processing batch {i+1} to {min(i+chunk_size, len(unprocessed_tickers))}...")
        
        enriched_data = get_deepseek_taxonomy(chunk_payload)
        
        if enriched_data:
            # Update our isolated dictionary
            for ticker, data in enriched_data.items():
                deepseek_data[ticker] = {
                    "deepseek_subsector": data.get("deepseek_subsector", "Unknown"),
                    "deepseek_rationale": data.get("deepseek_rationale", "No rationale provided.")
                }
            
            # Save progress after every single chunk!
            with open(DEEPSEEK_JSON, 'w', encoding='utf-8') as f:
                json.dump(deepseek_data, f, indent=4)
                
        # Politeness sleep for API rate limits
        time.sleep(2)

    print(f"\n✅ Success! DeepSeek taxonomy locked in at: {DEEPSEEK_JSON}")

if __name__ == '__main__':
    run_taxonomy_enrichment()