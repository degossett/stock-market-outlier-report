import os
import sys
import json
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "iShares-Russell-3000-ETF_fund.xls")
JSON_OUTPUT_PATH = os.path.join(BASE_DIR, "ishares_base_list.json")

def get_russell_data():
    if not os.path.exists(EXCEL_PATH):
        print(f"[ERROR] File not found at: {EXCEL_PATH}")
        print(">>> Please manually download the holdings file from iShares and place it in the folder.")
        sys.exit(1)  # <--- Forces the orchestrator to halt
        
    print(f"[INFO] Found local file at: {EXCEL_PATH}")
    print("[INFO] Using BeautifulSoup to slice through the XML spreadsheet...")
    
    try:
        with open(EXCEL_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f, 'xml')
            
        worksheets = soup.find_all('Worksheet')
        holdings_sheet = next((ws for ws in worksheets if ws.get('ss:Name') == 'Holdings'), None)
                
        if not holdings_sheet:
            print("[ERROR] Could not find the 'Holdings' tab in the XML.")
            sys.exit(1)
            
        rows = holdings_sheet.find_all('Row')
        print(f"[INFO] Found {len(rows)} rows. Searching for headers...")
        
        ticker_idx = name_idx = sector_idx = -1
        base_dict = {}
        
        for row in rows:
            cells = [data_tag.text.strip() for data_tag in row.find_all('Data')]
            if not cells: continue
                
            if ticker_idx == -1:
                lower_cells = [str(c).lower() for c in cells]
                if 'ticker' in lower_cells:
                    ticker_idx = lower_cells.index('ticker')
                    if 'name' in lower_cells: name_idx = lower_cells.index('name')
                    if 'sector' in lower_cells: sector_idx = lower_cells.index('sector')
                continue
            
            if len(cells) > ticker_idx:
                raw_ticker = cells[ticker_idx]
                if raw_ticker and len(raw_ticker) < 6 and raw_ticker != '-':
                    clean_ticker = raw_ticker.replace('.', '-')
                    name = cells[name_idx] if name_idx != -1 and len(cells) > name_idx else "Unknown"
                    sector = cells[sector_idx] if sector_idx != -1 and len(cells) > sector_idx else "Unknown"
                    
                    base_dict[clean_ticker] = {
                        "company_name": name,
                        "ishares_sector": sector
                    }
                    
        print(f"[INFO] Successfully extracted {len(base_dict)} unique companies.")
        return base_dict
        
    except Exception as e:
        print(f"[ERROR] Error parsing the XML file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 01.0: iShares Parsing...")
    company_dict = get_russell_data()
    
    if company_dict:
        with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(company_dict, f, indent=4)
        print(f"[SUCCESS] Base list saved to: {JSON_OUTPUT_PATH}")