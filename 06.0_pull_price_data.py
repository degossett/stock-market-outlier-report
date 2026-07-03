import os
import json
import sqlite3
import time
from datetime import datetime
import yfinance as yf
import pandas as pd

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TAXONOMY_JSON = os.path.join(BASE_DIR, "master_taxonomy_combined.json") 
DB_PATH = os.path.join(BASE_DIR, "market_noise.db")

def setup_database():
    """Connects to SQLite and ensures a clean slate for today's data."""
    print(">>> Preparing database (Flushing old data)...")
    
    # Attempt to delete the physical file first
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception as e:
            print(f"  [~] Warning: Could not delete old DB file: {e}")
            print("  [~] Proceeding with SQL DROP TABLE fallback...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS daily_prices")
    
    cursor.execute('''
        CREATE TABLE daily_prices (
            ticker TEXT,
            datetime TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON daily_prices (ticker)')
    
    conn.commit()
    return conn

def pull_price_data():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 06.0: 5-Minute Price Data Extraction...")
    
    if not os.path.exists(TAXONOMY_JSON):
        print(f"❌ [FATAL ERROR] Taxonomy file not found at: {TAXONOMY_JSON}")
        return

    with open(TAXONOMY_JSON, 'r', encoding='utf-8') as f:
        taxonomy = json.load(f)

    tickers = list(taxonomy.keys())
    print(f">>> Found {len(tickers)} companies to process.")
    
    try:
        conn = setup_database()
    except sqlite3.OperationalError as e:
        print(f"❌ [DATABASE LOCKED] SQLite Error: {e}")
        return

    print(">>> Firing up Yahoo Finance API in batch mode (Throttled for safety)...")
    
    # 1. REDUCE CHUNK SIZE TO 25
    chunk_size = 25
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    total_records_inserted = 0
    
    for idx, chunk in enumerate(ticker_chunks):
        print(f"  ... Downloading chunk {idx + 1}/{len(ticker_chunks)} ({len(chunk)} tickers)")
        
        # 2. DISABLE THREADING TO PREVENT RATE LIMIT BANS
        data = yf.download(
            chunk, 
            period="1d", 
            interval="5m", 
            group_by='ticker', 
            progress=False,
            threads=False
        )
        
        records_to_insert = []
        
        if len(chunk) == 1 or isinstance(data.columns, pd.Index) and not isinstance(data.columns, pd.MultiIndex):
            ticker = chunk[0]
            df = data.dropna()
            for index, row in df.iterrows():
                records_to_insert.append((
                    ticker,
                    str(index),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    int(row['Volume'])
                ))
        else:
            for ticker in chunk:
                if ticker in data.columns.levels[0]:
                    df = data[ticker].dropna()
                    for index, row in df.iterrows():
                        if not pd.isna(row['Open']):
                            records_to_insert.append((
                                ticker,
                                str(index),
                                float(row['Open']),
                                float(row['High']),
                                float(row['Low']),
                                float(row['Close']),
                                int(row['Volume'])
                            ))
                            
        if records_to_insert:
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT INTO daily_prices (ticker, datetime, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', records_to_insert)
            conn.commit()
            total_records_inserted += len(records_to_insert)
            
        # 3. INCREASE REST PERIOD TO 2.5 SECONDS
        time.sleep(2.5)

    conn.close()
    print(f"\n✅ Success! {total_records_inserted} rows of 5-minute intraday data saved to {DB_PATH}.")

if __name__ == '__main__':
    pull_price_data()