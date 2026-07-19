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

    # --- HTML TEMPLATE (GDELT Mobile-First Specification) ---
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quantitative Anomaly Report</title>
    <style>
        /* Mobile-First Base Settings */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f6f9;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
            -webkit-text-size-adjust: 100%;
        }}
        
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            box-sizing: border-box;
        }}

        /* Header Styling */
        .header {{
            background-color: #0f172a;
            color: #ffffff;
            padding: 24px 16px;
            text-align: left;
        }}
        .header h1 {{
            font-size: 20px;
            font-weight: 700;
            margin: 0 0 4px 0;
            letter-spacing: -0.5px;
            color: #f8fafc;
        }}
        .header .date {{
            font-size: 13px;
            color: #94a3b8;
            font-weight: 500;
        }}

        /* Section Containers */
        .section-title {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
            font-weight: 700;
            padding: 16px 16px 8px 16px;
            margin: 0;
            background-color: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
        }}

        .macro-box {{
            padding: 16px;
            font-size: 15px;
            line-height: 1.6;
            color: #334155;
            border-bottom: 8px solid #f1f5f9;
        }}

        /* Anomaly Cards */
        .anomaly-card {{
            padding: 16px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .anomaly-card:last-child {{
            border-bottom: none;
        }}

        /* Card Header Row */
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }}
        .ticker-zone {{
            display: flex;
            flex-direction: column;
        }}
        .ticker {{
            font-size: 18px;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.2;
        }}
        .company-name {{
            font-size: 12px;
            color: #64748b;
            margin-top: 2px;
        }}

        /* Button Layouts (Stack natively on tiny screens) */
        .action-buttons {{
            display: flex;
            gap: 6px;
        }}
        .action-btn {{
            display: inline-block;
            padding: 6px 10px;
            font-size: 12px;
            font-weight: 600;
            text-decoration: none;
            border-radius: 4px;
            text-align: center;
        }}
        .chart-btn {{
            background-color: #2563eb;
            color: #ffffff;
        }}
        .news-btn {{
            background-color: #f1f5f9;
            color: #334155;
            border: 1px solid #cbd5e1;
        }}

        /* Metadata Tags */
        .metadata {{
            margin-bottom: 10px;
            font-size: 12px;
            color: #475569;
            font-weight: 500;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
        }}
        .badge-sector {{
            background-color: #f1f5f9;
            padding: 2px 6px;
            border-radius: 3px;
            color: #64748b;
        }}
        .badge-flyer {{
            background-color: #fee2e2;
            color: #991b1b;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 600;
        }}

        /* Content Text */
        .analysis-text {{
            font-size: 14.5px;
            line-height: 1.55;
            color: #334155;
            margin-bottom: 12px;
        }}

        .rationale-box {{
            background-color: #f8fafc;
            border-left: 3px solid #cbd5e1;
            padding: 8px 12px;
            font-size: 13px;
            line-height: 1.5;
            color: #475569;
        }}

        /* Footer */
        .footer {{
            background-color: #0f172a;
            color: #94a3b8;
            font-size: 12px;
            text-align: center;
            padding: 20px 16px;
            border-top: 1px solid #e2e8f0;
        }}

        /* Precision Mobile Adjustments */
        @media only screen and (max-width: 480px) {{
            .card-header {{
                flex-direction: column;
                gap: 10px;
            }}
            .action-buttons {{
                width: 100%;
            }}
            .action-btn {{
                flex: 1;
                padding: 8px 4px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Quantitative Anomaly Report</h1>
            <div class="date">{report_date}</div>
        </div>

        <div class="section-title">Macro Market Narrative</div>
        <div class="macro-box">
            {macro_narrative}
        </div>

        <div class="section-title">Idiosyncratic Anomalies Extracted</div>
        <div class="anomalies-list">
"""

    for item in anomalies:
        ticker = item.get("ticker", "UNKNOWN")
        company = item.get("company_name", "")
        sector = item.get("sector", "General")
        subsector = item.get("subsector", "")
        analysis = item.get("analysis", "")
        rationale = item.get("rationale", "")
        is_frequent_flyer = item.get("frequent_flyer", False)

        # Generate cleaner, standard finance external tracker URLs
        chart_url = f"https://finance.yahoo.com/quote/{ticker}/chart"
        news_url = f"https://finance.yahoo.com/quote/{ticker}/news"

        memory_badge = '<span class="badge-flyer">⚠️ Frequent Flyer</span>' if is_frequent_flyer else ''
        subsector_str = f" &bull; {subsector}" if subsector else ""

        html_content += f"""
            <div class="anomaly-card">
                <div class="card-header">
                    <div class="ticker-zone">
                        <span class="ticker">{ticker}</span>
                        <span class="company-name">{company}</span>
                    </div>
                    <div class="action-buttons">
                        <a href="{chart_url}" target="_blank" class="action-btn chart-btn">Chart</a>
                        <a href="{news_url}" target="_blank" class="action-btn news-btn">News</a>
                    </div>
                </div>
                <div class="metadata">
                    <span class="badge-sector">{sector}{subsector_str}</span>
                    {memory_badge}
                </div>
                <div class="analysis-text">
                    {analysis}
                </div>
        """
        
        if rationale and rationale != "Unknown":
            html_content += f"""
                <div class="rationale-box">
                    <strong>Context:</strong> {rationale}
                </div>
            """
            
        html_content += """
            </div>
        """

    html_content += f"""
        </div>
        <div class="footer">
            Automated Extraction Pipeline &bull; {len(anomalies)} Material Anomalies Isolated
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
