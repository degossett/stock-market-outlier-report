import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from upstash_redis import Redis

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

INPUT_JSON = os.path.join(BASE_DIR, "deep_research_analysis.json")
TAXONOMY_JSON = os.path.join(BASE_DIR, "master_taxonomy_hierarchical.json") 
OUTPUT_JSON = os.path.join(BASE_DIR, "glm_newsletter_finalists.json")

# Initialize Direct Z.ai Client
client = OpenAI(
    api_key=os.getenv("ZAI_API_KEY"),
    base_url="https://api.z.ai/api/paas/v4/"
)

# Initialize Upstash Redis (Memory)
# If credentials are missing, it will gracefully fail later and default to a count of 1
try:
    redis = Redis(
        url=os.getenv("UPSTASH_REDIS_REST_URL"), 
        token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
    )
except Exception as e:
    redis = None
    print(f"⚠️ Redis connection not initialized: {e}")

MODEL_NAME = "glm-5.2"
SEVEN_DAYS_IN_SECONDS = 604800

def run_editor_in_chief():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 10.0: Editor-in-Chief (GLM 5.2)...")
    
    if not os.path.exists(INPUT_JSON):
        print(f"⚠️ Input file missing at: {INPUT_JSON}. Run Script 09 first.")
        return
        
    if not os.path.exists(TAXONOMY_JSON):
        print(f"⚠️ Taxonomy file missing at: {TAXONOMY_JSON}.")
        return

    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        all_evaluations = json.load(f)
        
    with open(TAXONOMY_JSON, 'r', encoding='utf-8') as f:
        master_metadata = json.load(f)
        
    material_movers = {ticker: desc for ticker, desc in all_evaluations.items() if desc != "NOISE"}
    
    if not material_movers:
        print(">>> No material movers found today. The market was completely flat!")
        return
        
    print(f">>> Feeding {len(material_movers)} material anomalies to GLM 5.2 for final curation...")

    prompt = f"""
You are the Editor-in-Chief of an elite quantitative finance newsletter. 
Below is a dictionary of the day's most anomalous stock movements, pre-filtered by your junior analysts. The data includes the ticker and a paragraph explaining why the move was structurally significant.

Your tasks:
1. Read all the reports to understand the overarching macroeconomic or sector-specific themes of the day.
2. Write a single 'macro_narrative' paragraph summarizing these themes.
3. Select the ABSOLUTE TOP 20 most explosive, undeniable anomalies from the list.
   * CRITICAL RULE: You do NOT have to select 20. If only 6 stocks are truly material, only return 6.
   * Rank them in order of importance/severity.
4. Output the exact original paragraph provided for each selected ticker.

RETURN ONLY A VALID JSON OBJECT matching this exact structure:
{{
    "macro_narrative": "Your summary paragraph here...",
    "top_anomalies": [
        {{
            "ticker": "XYZ",
            "paragraph": "The exact original paragraph text..."
        }}
    ]
}}

Daily Anomaly Reports:
{json.dumps(material_movers, indent=2)}
"""

    try:
        print("  ... Waiting for GLM 5.2 to synthesize the market and curate the finalists...")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        raw_output = response.choices[0].message.content.strip()
        
        start_idx = raw_output.find('{')
        end_idx = raw_output.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("The AI response did not contain a valid JSON object structure.")
            
        clean_json = raw_output[start_idx:end_idx + 1].strip()
        final_data = json.loads(clean_json)
        
        # --- ENRICHMENT & MEMORY INJECTION ---
        print(">>> Checking Redis memory for Frequent Flyers...")
        for anomaly in final_data.get("top_anomalies", []):
            ticker = anomaly.get("ticker")
            meta = master_metadata.get(ticker, {})
            
            anomaly["company_name"] = meta.get("company_name", "Unknown")
            anomaly["ishares_sector"] = meta.get("ishares_sector", "Unknown")
            anomaly["deepseek_subsector"] = meta.get("deepseek_subsector", "Unknown")
            anomaly["deepseek_rationale"] = meta.get("deepseek_rationale", "Unknown")
            
            # Redis Memory Logic
            appearance_count = 1
            if redis:
                try:
                    # Increment the counter for this ticker
                    appearance_count = redis.incr(ticker)
                    # Reset the 7-day expiration clock
                    redis.expire(ticker, SEVEN_DAYS_IN_SECONDS)
                except Exception as e:
                    print(f"  [~] Warning: Redis communication failed for {ticker}: {e}")
                    
            anomaly["appearance_count"] = appearance_count
        # ------------------------------------
        
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4)
            
        anomaly_count = len(final_data.get("top_anomalies", []))
        print(f"\n✅ Success! GLM 5.2 selected {anomaly_count} finalists. Memory updated.")
        print(f"Results saved to: {OUTPUT_JSON}")
        
    except json.JSONDecodeError:
        print(f"❌ JSON Parsing Error. Raw snippet: {raw_output[:200]}...")
    except Exception as e:
        print(f"❌ Error during Editor-in-Chief synthesis: {e}")

if __name__ == '__main__':
    run_editor_in_chief()