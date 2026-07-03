import subprocess
import os
import sys
import time
from datetime import datetime, timedelta
import pandas_market_calendars as mcal

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "pipeline_execution.log")

# List every script in the exact logical order it must execute
PIPELINE_SCRIPTS = [
    "01.0_parse_ishares.py",                 
    "02.0_enrich_with_yahoo.py",              
    "03.0_deepseek_taxonomy.py",              
    "04.0_combine_metadata.py",     
    "05.0_gemini_sector.py",              
    "06.0_pull_price_data.py",           
    "07.0_generate_individual_charts.py",         
    "08.0_field_reporter.py",               
    "09.0_materiality_filter.py",                     
    "10.0_editor_in_chief.py",                
    "11.0_generate_newsletter.py"             
]

class Logger(object):
    """A dual-output logger that prints to the terminal AND writes to a text file."""
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def check_market_was_open_yesterday():
    """Checks the official NYSE holiday calendar to see if the market traded yesterday."""
    print(">>> Querying official NYSE calendar...")
    
    # Get the official New York Stock Exchange calendar
    nyse = mcal.get_calendar('NYSE')
    
    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')
    
    # Check if yesterday was a valid trading day
    # valid_days returns an index of open days. If our date is in it, the market was open!
    open_days = nyse.valid_days(start_date=date_str, end_date=date_str)
    
    if len(open_days) > 0:
        print(f"  [+] Confirmed: NYSE was OPEN on {date_str}.")
        return True
    else:
        print(f"  [-] Confirmed: NYSE was CLOSED on {date_str} (Weekend or Holiday).")
        return False

def cleanup_yesterdays_analysis():
    """Sweeps out the daily AI analysis JSONs so the pipeline doesn't read stale data."""
    stale_files = [
        "qwen_visual_overviews.json",
        "deepseek_material_movers.json",
        "glm_newsletter_finalists.json"
    ]
    
    print(">>> Sweeping out yesterday's analysis files...")
    for file in stale_files:
        file_path = os.path.join(BASE_DIR, file)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"  [+] Deleted {file}")

def run_pipeline():
    # Redirect all print statements to both the terminal and the log file
    sys.stdout = Logger(LOG_FILE)
    sys.stderr = sys.stdout 

    print("================================================================================")
    print(f"📅 SYSTEM DATE CHECK: Today is {datetime.now().strftime('%A, %B %d, %Y')}")
    print("================================================================================")
    
    # --- OUR NEW SMART GUARDRAIL ---
    if not check_market_was_open_yesterday():
        print("\n🛑 Guardrail triggered. The market was closed yesterday.")
        print(">>> Halting pipeline execution to prevent duplicate data runs.")
        sys.exit(0)
    
    print("\n🟢 Guardrail passed. Fresh market session data available. Proceeding...\n")
    
    # --- AUTOMATED CLEANUP ---
    cleanup_yesterdays_analysis()
    
    print("================================================================================")
    print(f"🏭 KICKING OFF QUANTITATIVE ANOMALY EXTRACTION PIPELINE")
    print(f"Session Triggered: {datetime.now().strftime('%H:%M:%S')}")
    print("================================================================================\n")

    start_time = time.time()
    performance_log = []

    for script in PIPELINE_SCRIPTS:
        script_path = os.path.join(BASE_DIR, script)
        print(f"================================================================================")
        print(f"🚀 RUNNING STEP: {script}")
        print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"================================================================================\n")
        
        step_start = time.time()
        
        try:
            # Force python to use UTF-8 encoding to prevent Windows Terminal crashes
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            result = subprocess.run(
                ["python", script_path], 
                check=True, 
                text=True, 
                capture_output=True,
                env=env
            )
            print(result.stdout)
            
            step_duration = time.time() - step_start
            performance_log.append((script, step_duration, True))
            print(f"✅ Step {script} completed successfully in {step_duration:.2f} seconds.\n")
            
        except subprocess.CalledProcessError as e:
            step_duration = time.time() - step_start
            performance_log.append((script, step_duration, False))
            
            print(e.stdout)
            print(f"\n❌ [FATAL ERROR] Step {script} crashed! (Exit Code {e.returncode})")
            print(f"🚨 Pipeline execution halted at {datetime.now().strftime('%H:%M:%S')}")
            print(e.stderr)
            break 
        except FileNotFoundError:
            print(f"\n❌ [FATAL ERROR] Could not find the script: {script_path}")
            print(f"🚨 Pipeline execution halted.")
            break

    total_duration = time.time() - start_time
    
    print("\n================================================================================")
    print("📊 PIPELINE EXECUTION PERFORMANCE SUMMARY")
    print("================================================================================")
    
    for script_name, duration, success in performance_log:
        status = "🟢 SUCCESS" if success else "🔴 FAILED "
        print(f"  {status} |  {duration:>7.2f}s | {script_name}")
        
    print("-" * 80)
    print(f"Total Combined Pipeline Runtime: {total_duration / 60:.2f} minutes")
    print("================================================================================")

    # Restore default stdout when finished
    sys.stdout = sys.stdout.terminal

if __name__ == "__main__":
    run_pipeline()