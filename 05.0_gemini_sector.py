import os
import json
import time
import re
from datetime import datetime
from dotenv import load_dotenv

# Import the new, actively maintained Google GenAI SDK!
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the new client
client = genai.Client(api_key=GEMINI_API_KEY)

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "master_taxonomy_combined.json")

# The dedicated folder for our checkpoint files
TEMP_DIR = os.path.join(BASE_DIR, "ishares_sectors") 
FINAL_HIERARCHY_JSON = os.path.join(BASE_DIR, "master_taxonomy_hierarchical.json")

def sanitize_filename(name):
    """Cleans up sector names so they can be saved as valid file names."""
    return re.sub(r'[^a-zA-Z0-9]', '_', name)

def group_by_ishares_sector(master_data):
    """Pass 1: Get the lay of the land by grouping all stocks by their iShares sector."""
    print(">>> Pass 1: Grouping landscape by iShares Sector...")
    sector_groups = {}
    
    for ticker, data in master_data.items():
        sector = data.get("ishares_sector", "Unclassified") 
        if sector not in sector_groups:
            sector_groups[sector] = {}
        sector_groups[sector][ticker] = data
        
    print(f">>> Found {len(sector_groups)} unique iShares Sectors.")
    return sector_groups

def process_sectors_with_gemini(sector_groups):
    """Pass 2: Send each sector to Gemini 3.1 Pro to generate sub-sectors and map the stocks."""
    print("\n>>> Pass 2: Processing each iShares Sector through Gemini 3.1 Pro...")
    
    # Create the dedicated folder if it doesn't exist
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        
    # Pointing to the top-tier 3.1 Pro Preview model
    model_id = "gemini-3.1-pro-preview"
    
    for sector_name, companies in sector_groups.items():
        safe_name = sanitize_filename(sector_name)
        temp_file_path = os.path.join(TEMP_DIR, f"{safe_name}.json")
        
        # Checkpoint logic: Skip if we already processed this sector!
        if os.path.exists(temp_file_path):
            print(f"  [~] Skipping '{sector_name}' - Already processed.")
            continue
            
        print(f"  [+] Processing '{sector_name}' ({len(companies)} companies)...")
        
        # Strip the payload down to exactly what Gemini needs to make its decision
        payload = {}
        for t, d in companies.items():
            payload[t] = {
                "name": d.get("company_name"),
                "yahoo_industry": d.get("yahoo_industry"),
                "deepseek_subsector": d.get("deepseek_subsector"),
                "rationale": d.get("deepseek_rationale")
            }
            
        prompt = f"""
        You are an elite institutional portfolio architect. Your job is to organize the companies within the '{sector_name}' macroeconomic category.
        
        Below is a JSON containing all the companies in this category, including their legacy industries and a description of what they do.
        
        Your tasks:
        1. Read through all the companies.
        2. Define a clean, logical menu of 5 to 12 standardized "Sectors" that perfectly organize these specific companies. (e.g. if the category is Tech, you might create 'Semiconductors', 'Cloud Software', etc.).
        3. Assign EVERY SINGLE TICKER provided to exactly one of the sectors you just created.
        
        RETURN ONLY A VALID JSON OBJECT matching this exact structure:
        {{
            "defined_sectors": [
                "Sector 1",
                "Sector 2"
            ],
            "company_mappings": {{
                "TICKER1": "Sector 1",
                "TICKER2": "Sector 2"
            }}
        }}
        
        Company Data for '{sector_name}':
        {json.dumps(payload, indent=2)}
        """
        
        try:
            # Using the new google-genai Client generation syntax
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            # Clean and parse the output
            raw_output = response.text.replace('```json', '').replace('```', '').strip()
            parsed_data = json.loads(raw_output)
            
            # Save the sector payload to our dedicated folder
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=4)
                
        except Exception as e:
            print(f"  ❌ Error processing '{sector_name}': {e}")
            
        # Give the API a brief rest between massive sector chunks
        time.sleep(5)

def build_final_hierarchy(master_data):
    """Pass 3: Stitch the local temp files and the master data into the final nested JSON."""
    print("\n>>> Pass 3: Compiling sector files into the final hierarchy...")
    
    if not os.path.exists(TEMP_DIR):
        print("⚠️ Sector directory not found. Did Pass 2 run successfully?")
        return
        
    final_hierarchy = {}
    
    # Loop through the original master data and inject the Gemini sectors
    for ticker, base_info in master_data.items():
        ishares_sector = base_info.get("ishares_sector", "Unclassified")
        safe_name = sanitize_filename(ishares_sector)
        temp_file_path = os.path.join(TEMP_DIR, f"{safe_name}.json")
        
        gemini_sector = "Unmapped" 
        
        if os.path.exists(temp_file_path):
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                sector_data = json.load(f)
                gemini_sector = sector_data.get("company_mappings", {}).get(ticker, "Unmapped")
                
        # Build the branches: iShares Sector -> Gemini Sector -> Ticker
        if ishares_sector not in final_hierarchy:
            final_hierarchy[ishares_sector] = {}
            
        if gemini_sector not in final_hierarchy[ishares_sector]:
            final_hierarchy[ishares_sector][gemini_sector] = {}
            
        # Add the full company metadata to the tip of the branch
        base_info["gemini_sector"] = gemini_sector
        final_hierarchy[ishares_sector][gemini_sector][ticker] = base_info
        
    # Write the master file
    with open(FINAL_HIERARCHY_JSON, 'w', encoding='utf-8') as f:
        json.dump(final_hierarchy, f, indent=4)
        
    print(f"✅ Success! Hierarchical taxonomy saved to: {FINAL_HIERARCHY_JSON}")

def run_gemini_pipeline():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 06.0: Gemini Tiered Taxonomy...")
    
    if not os.path.exists(INPUT_JSON):
        print(f"⚠️ Source file missing at: {INPUT_JSON}. Run Script 05 first.")
        return
        
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        master_data = json.load(f)
        
    # Pass 1: Group
    sector_groups = group_by_ishares_sector(master_data)
    
    # Pass 2: Gemini Analysis (Checkpointed to the new folder)
    process_sectors_with_gemini(sector_groups)
    
    # Pass 3: Final Assembly
    build_final_hierarchy(master_data)

if __name__ == '__main__':
    run_gemini_pipeline()