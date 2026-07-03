import os
import json
from datetime import datetime, timedelta

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "glm_newsletter_finalists.json")
OUTPUT_HTML = os.path.join(BASE_DIR, "daily_anomaly_newsletter.html")

def generate_html_report():
    yesterday = datetime.now() - timedelta(days=1)
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 11.0: Newsletter HTML Generation...")
    
    if not os.path.exists(INPUT_JSON):
        print(f"⚠️ Input file missing at: {INPUT_JSON}. Run Script 10 first.")
        return

    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        report_data = json.load(f)

    macro_narrative = report_data.get("macro_narrative", "No macro narrative provided today.")
    anomalies = report_data.get("top_anomalies", [])
    
    report_date = yesterday.strftime("%A, %B %d, %Y")

    # --- HTML TEMPLATE ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Market Anomalies</title>
        <style>
            body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333333; }}
            .container {{ max-width: 800px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
            .header {{ background-color: #0f172a; color: #ffffff; padding: 30px 40px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; letter-spacing: 1px; }}
            .header p {{ margin: 10px 0 0 0; font-size: 14px; color: #94a3b8; }}
            .macro-section {{ background-color: #f8fafc; padding: 30px 40px; border-bottom: 1px solid #e2e8f0; }}
            .macro-section h2 {{ margin-top: 0; color: #0f172a; font-size: 20px; }}
            .macro-section p {{ line-height: 1.6; color: #475569; margin-bottom: 0; }}
            .anomalies-section {{ padding: 20px 40px; }}
            .anomaly-card {{ padding: 25px 0; border-bottom: 1px solid #e2e8f0; }}
            .anomaly-card:last-child {{ border-bottom: none; }}
            .ticker-header {{ display: flex; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 10px; }}
            .ticker-badge {{ background-color: #2563eb; color: #ffffff; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 16px; }}
            .company-name {{ font-size: 20px; font-weight: 600; color: #0f172a; margin: 0; flex-grow: 1; }}
            .action-buttons {{ display: flex; gap: 8px; }}
            .action-btn {{ text-decoration: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; transition: background-color 0.2s; }}
            .chart-btn {{ background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }}
            .chart-btn:hover {{ background-color: #e2e8f0; color: #0f172a; }}
            .news-btn {{ background-color: #e0e7ff; color: #1d4ed8; border: 1px solid #bfdbfe; }}
            .news-btn:hover {{ background-color: #dbeafe; color: #1e40af; }}
            .frequent-flyer {{ background-color: #fef2f2; color: #dc2626; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid #fecaca; }}
            .metadata {{ font-size: 13px; color: #64748b; margin-bottom: 15px; font-weight: 500; display: flex; gap: 10px; align-items: center; }}
            .analysis-text {{ line-height: 1.6; color: #334155; font-size: 15px; }}
            .rationale-box {{ margin-top: 15px; padding: 12px 15px; background-color: #f1f5f9; border-left: 4px solid #94a3b8; font-size: 13px; color: #475569; font-style: italic; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #94a3b8; background-color: #f8fafc; border-top: 1px solid #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>QUANTITATIVE ANOMALY REPORT</h1>
                <p>{report_date}</p>
            </div>
            <div class="macro-section">
                <h2>Macroeconomic Overview</h2>
                <p>{macro_narrative}</p>
            </div>
            <div class="anomalies-section">
    """

    for item in anomalies:
        ticker = item.get("ticker", "UNKNOWN")
        company = item.get("company_name", "Unknown Company")
        sector = item.get("ishares_sector", "Unknown Sector")
        subsector = item.get("deepseek_subsector", "Unknown Sub-Sector")
        analysis = item.get("paragraph", "No analysis provided.")
        rationale = item.get("deepseek_rationale", "")
        count = item.get("appearance_count", 1)
        
        chart_url = f"https://finance.yahoo.com/quote/{ticker}/chart?range=5d"
        news_url = f"https://finance.yahoo.com/quote/{ticker}/news/"

        # The Frequent Flyer Badge Logic
        memory_badge = f'<span class="frequent-flyer">🔥 {count}x in 7 Days</span>' if count > 1 else ""

        html_content += f"""
                <div class="anomaly-card">
                    <div class="ticker-header">
                        <span class="ticker-badge">{ticker}</span>
                        <h3 class="company-name">{company}</h3>
                        <div class="action-buttons">
                            <a href="{chart_url}" target="_blank" class="action-btn chart-btn">View Chart</a>
                            <a href="{news_url}" target="_blank" class="action-btn news-btn">Stock News</a>
                        </div>
                    </div>
                    <div class="metadata">
                        <span>{sector} &bull; {subsector}</span>
                        {memory_badge}
                    </div>
                    <div class="analysis-text">
                        {analysis}
                    </div>
        """
        
        if rationale and rationale != "Unknown":
            html_content += f"""
                    <div class="rationale-box">
                        <strong>Company Profile:</strong> {rationale}
                    </div>
            """
            
        html_content += """
                </div>
        """

    html_content += f"""
            </div>
            <div class="footer">
                Automated Extraction Pipeline &bull; {len(anomalies)} Material Anomalies Detected
            </div>
        </div>
    </body>
    </html>
    """

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"✅ Success! HTML Newsletter generated with {len(anomalies)} stocks.")
    print(f"File saved to: {OUTPUT_HTML}")

if __name__ == '__main__':
    generate_html_report()