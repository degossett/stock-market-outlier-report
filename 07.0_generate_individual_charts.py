import os
import shutil
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "market_noise.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "vlm_individual_charts")

def generate_visuals():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 08.0: The Printing Press (Matplotlib)...")
    
    if not os.path.exists(DB_PATH):
        print("⚠️ Database missing. Run Script 07 first.")
        return

    # NEW: Automated Trash Collection
    # If the folder exists, we vaporize it and everything inside to prevent stale charts
    if os.path.exists(OUTPUT_DIR):
        print(f">>> Sweeping out yesterday's stale charts from {OUTPUT_DIR}...")
        shutil.rmtree(OUTPUT_DIR)
        
    # Recreate a perfectly clean, empty folder for today's run
    os.makedirs(OUTPUT_DIR)

    conn = sqlite3.connect(DB_PATH)
    
    # Get a unique list of all tickers in the database today
    tickers_df = pd.read_sql_query("SELECT DISTINCT ticker FROM daily_prices", conn)
    tickers = tickers_df['ticker'].tolist()
    
    print(f">>> Found {len(tickers)} unique stocks in the database. Generating charts...")

    for i, ticker in enumerate(tickers):
        # Print every 100th chart to keep the console clean
        if (i + 1) % 100 == 0 or i == 0:
            print(f"  ... Printing chart [{i+1}/{len(tickers)}]: {ticker}")
            
        # Grab today's prices for this specific ticker
        query = f"SELECT datetime, open, close FROM daily_prices WHERE ticker = '{ticker}' ORDER BY datetime ASC"
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            continue
            
        # Calculate percentage change from yesterday's close (the first row in our DB pull)
        open_price = df['open'].iloc[0]
        
        # Prevent division by zero
        if open_price == 0:
            continue
            
        df['pct_change'] = ((df['close'] - open_price) / open_price) * 100

        # --- PLOTTING ---
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('white')
        
        ax.plot(df['datetime'], df['pct_change'], color='black', linewidth=1.5)
        
        # Standardize the Y-axis mathematically so the AI knows the boundaries
        ax.set_ylim(-15, 15)
        
        # The zero-line represents yesterday's closing price
        ax.axhline(0, color='red', linestyle='--', alpha=0.5)
        
        # Hide axes completely to prevent OCR distraction
        ax.axis('off')
        plt.tight_layout()

        # Save to the fresh hard drive folder
        save_path = os.path.join(OUTPUT_DIR, f"{ticker}.png")
        plt.savefig(save_path, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        
    conn.close()
    print(f"\n✅ Success! All {len(tickers)} physical charts saved to a clean folder: {OUTPUT_DIR}")

if __name__ == '__main__':
    generate_visuals()