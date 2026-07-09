import os
import sys
import subprocess
import time
from datetime import datetime

# --- PIPELINE ROUTING ---
SUNDAY_SCRIPTS = [
    "01.0_parse_ishares.py",                 
    "02.0_enrich_with_yahoo.py",              
    "03.0_deepseek_taxonomy.py",              
    "04.0_combine_metadata.py",              
    "05.0_gemini_sector.py"
]

DAILY_SCRIPTS = [     
    "06.0_pull_price_data.py",           
    "07.0_generate_individual_charts.py",         
    "08.0_field_reporter.py",                 
    "09.0_materiality_filter.py",                     
    "10.0_editor_in_chief.py",                
    "11.0_generate_newsletter.py"             
]

def get_todays_route():
    """Determines which set of scripts to run based on the day of the week."""
    current_day = datetime.now().strftime("%A")
    print("="*80)
    print(f"📅 SYSTEM DATE CHECK: Today is {current_day}")
    print("="*80)
    
    if current_day == "Sunday":
        print("🛠️ Sunday detected. Routing to Weekly Taxonomy & Metadata Build.")
        return SUNDAY_SCRIPTS
    elif current_day == "Monday":
        print("🛑 Monday detected. Market was closed yesterday. Sleeping.")
        sys.exit(0)
    else:
        print("📈 Weekday detected. Routing to Daily Anomaly Processing.")
        # Note: Your holiday guardrail inside Script 06 will handle actual market holidays!
        return DAILY_SCRIPTS

# ... (Keep your existing run_script() and main() functions, just pass it the correct list!)

def main():
    # Get the correct list of scripts for today
    scripts_to_run = get_todays_route()
    
    pipeline_start = time.time()
    performance_log = []
    
    print("\n" + "="*80)
    print(f"🏭 KICKING OFF QUANTITATIVE ANOMALY EXTRACTION PIPELINE")
    # ... runs through scripts_to_run instead of PIPELINE_SCRIPTS
