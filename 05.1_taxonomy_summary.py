import os
import json
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "master_taxonomy_hierarchical.json")
OUTPUT_MD = os.path.join(BASE_DIR, "taxonomy_summary.md")

def generate_summary():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 06.1: Taxonomy Rollup Summary...")
    
    if not os.path.exists(INPUT_JSON):
        print(f"⚠️ Source file missing at: {INPUT_JSON}. Run Script 06 first.")
        return
        
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        master_data = json.load(f)
        
    report_lines = []
    report_lines.append(f"# 📊 Master Taxonomy Summary")
    report_lines.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    report_lines.append("---\n")
    
    total_market_count = 0
    
    # Sort categories alphabetically
    for category_name, sectors in sorted(master_data.items()):
        # Calculate total companies in this category
        cat_count = sum(len(companies) for companies in sectors.values())
        total_market_count += cat_count
        
        report_lines.append(f"## 🏢 {category_name} ({cat_count} companies)")
        
        # Sort sectors by the number of companies they contain (Largest to Smallest)
        sorted_sectors = sorted(sectors.items(), key=lambda item: len(item[1]), reverse=True)
        
        for sector_name, companies in sorted_sectors:
            report_lines.append(f"  * **{sector_name}**: {len(companies)} companies")
            
        report_lines.append("\n") # Add a blank line between categories
        
    report_lines.append("---\n")
    report_lines.append(f"### 📈 **Total Companies Processed:** {total_market_count}")

    # Write the report to a Markdown file
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        
    print(f"✅ Success! Summary report generated at: {OUTPUT_MD}")
    
    # Print a quick preview to the terminal
    print("\n--- PREVIEW ---")
    for line in report_lines[:15]: 
        print(line)
    print("...\n(Open 06.1_taxonomy_summary.md in VS Code to see the full list!)")

if __name__ == '__main__':
    generate_summary()