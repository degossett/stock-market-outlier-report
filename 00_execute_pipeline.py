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
    DAILY_SCRIPTS = [
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
        return DAILY_SCRIPTS

def run_script(script_name):
    """Executes a single python script and monitors its output in real time."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, script_name)
    
    if not os.path.exists(script_path):
        print(f"\n❌ [FATAL ERROR] Script missing from directory: {script_name}")
        return False, 0.0

    print("\n" + "="*80)
    print(f"🚀 RUNNING STEP: {script_name}")
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    start_time = time.time()
    
    process = subprocess.Popen(
        [sys.executable, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Stream the output directly to the terminal in real time
    for line in process.stdout:
        print(line, end="")
        
    process.wait()
    duration = time.time() - start_time
    
    if process.returncode == 0:
        print(f"\n✅ Step {script_name} completed successfully in {duration:.2f} seconds.")
        return True, duration
    else:
        print(f"\n❌ Step {script_name} CRASHED with exit code {process.returncode}.")
        return False, duration

def main():
    # Get the correct list of scripts for today
    scripts_to_run = get_todays_route()
    
    pipeline_start = time.time()
    performance_log = []
    
    print("\n" + "="*80)
    print(f"🏭 KICKING OFF QUANTITATIVE ANOMALY EXTRACTION PIPELINE")
    print(f"Session Triggered: {datetime.now().strftime('%A, %B %d, %Y %H:%M:%S')}")
    print("="*80)
    
    for script in scripts_to_run:
        success, duration = run_script(script)
        performance_log.append((script, success, duration))
        
        if not success:
            print("\n" + "!"*80)
            print(f"🚨 PIPELINE EXECUTION HALTED AT: {script}")
            print("Downstream dependencies protectively bypassed. Fix errors before resuming.")
            print("!"*80 + "\n")
            sys.exit(1)
            
    total_duration = time.time() - pipeline_start
    
    # --- FINAL PERFORMANCE REPORT ---
    print("\n" + "="*80)
    print("📊 PIPELINE EXECUTION PERFORMANCE SUMMARY")
    print("="*80)
    for script, success, duration in performance_log:
        status = "🟢 SUCCESS" if success else "🔴 FAILED "
        print(f"  {status} | {duration:7.2f}s | {script}")
    print("-"*80)
    print(f"Total Combined Pipeline Runtime: {total_duration/60:.2f} minutes")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
