# Quantitative Anomaly Extraction Pipeline (Stock Gap Analysis)

An automated, multi-agent AI data engineering pipeline that extracts, normalizes, and analyzes the entire Russell 3000 index to identify idiosyncratic market anomalies. By combining traditional quantitative data ingestion (Yahoo Finance API, SQLite) with frontier multimodal models (Qwen-VL, DeepSeek V4, GLM 5.2, and Gemini), this architecture digests over 2,500 intraday stock charts and curates a highly professional daily macro-narrative and "Top 20" anomaly newsletter.

---

## 🛑 The "Quant Reality Check": Data Sourcing & The Manual Failsafe

In quantitative finance, the exact constituent list of the Russell 3000 is proprietary intellectual property (owned by FTSE Russell) that typically costs tens of thousands of dollars to license. Our pipeline legally bypasses this by scraping the publicly mandated holdings of the **iShares Russell 3000 ETF (IWV)**.

However, enterprise asset managers like BlackRock employ aggressive Web Application Firewalls (WAFs) to block automated scraping (Selenium, requests, etc.). Fighting these bot-walls is a massive waste of data engineering resources because of one fundamental market reality:

**The Russell 3000 is a Slowly Changing Dimension (SCD).**
The index completely reconstitutes exactly once a year on the **4th Friday of June**. Because the constituent list is 99.9% static day-to-day, building and maintaining a daily automated scraper is an anti-pattern. 

**The Solution:**
1. Navigate to the [iShares Russell 3000 ETF Page](https://www.ishares.com/us/products/239714/ishares-russell-3000-etf).
2. Manually download the Holdings file.
3. Save it in the project root exactly as `iShares-Russell-3000-ETF_fund.xls`.
4. **Commit this file directly to your GitHub repository.** Because this is a "static configuration" file that rarely changes, committing it allows your headless Docker containers and GitHub Actions to access the baseline data automatically at 4:00 AM without human intervention.

### Git Configuration Note
Ensure your `.gitignore` file allows this specific file to be tracked, while keeping other potentially massive data dumps out:
```text
*.xls
*.xlsx
!iShares-Russell-3000-ETF_fund.xls
```

### Maintenance Routine
At a minimum, you must manually download the fresh `.xls` file and push it to the repository immediately following the annual reconstitution on the **4th Friday of June**. For tighter pipeline accuracy, performing this manual drop once a month takes 15 seconds and guarantees a perfectly clean baseline.

### A Note on Ticker Failures (Even Post-Reconstitution)
You will notice that even immediately following the late-June index reset, the pipeline will still drop a handful of tickers (usually around 15–20 out of 3,000). This is not a bug; it is a feature of robust error handling. These drops fall into three predictable buckets:
* **Class Share Mismatches:** iShares lists Berkshire Class B as `BRKB`, but Yahoo Finance requires `BRK-B`. 
* **Cash & Derivatives:** ETFs hold cash placeholders (`--`) and futures contracts (e.g., `ESU6`) for liquidity. These are not standard equities.
* **Rapid M&A / Delistings:** Micro-cap biotech companies get acquired or go bankrupt constantly, sometimes moving faster than the ETF's published CSV file.

The pipeline is designed to gracefully drop this "garbage data" and seamlessly continue processing the remaining ~2,560 valid U.S. equities.

---

## 🏗️ Pipeline Architecture

The pipeline is orchestrated by a master execution script (`00_execute_pipeline.py`) that strictly enforces environment encoding (`utf-8`) to prevent Windows Terminal crashes. It utilizes the `pandas_market_calendars` library as a dynamic guardrail, cross-referencing the official NYSE holiday calendar to mathematically ensure the market was open the previous day before executing.

### Phase 1: Metadata & Taxonomy Construction
* **`01.0_parse_ishares.py`**: Parses the natively downloaded iShares XML file using BeautifulSoup to extract base tickers, names, and sectors.
* **`02.0_enrich_with_yahoo.py`**: Pings Yahoo Finance to append live Market Cap data.
* **`03.0_deepseek_taxonomy.py`**: Leverages DeepSeek to generate custom sub-sectors and highly specific company rationales/profiles.
* **`04.0_combine_metadata.py`**: Flattens the parsed data, Yahoo data, and DeepSeek data into a unified JSON database.
* **`05.0_gemini_sector.py`**: Uses Google Gemini to dynamically group the landscape into a hierarchical taxonomy. *(Utility `05.1_taxonomy_summary.py` can be run manually to generate a Markdown tree of this structure).*

### Phase 2: Quantitative Data Ingestion & Visualization
* **`06.0_pull_price_data.py`**: Downloads the most recent trading session's 5-minute interval data for all ~2,560 equities via `yfinance` and stores it cleanly in a local SQLite database (`market_noise.db`). *Note: This script features strict IP throttling (batching and sleep timers) to safely navigate Yahoo Finance rate limits.*
* **`07.0_generate_individual_charts.py`**: Uses Matplotlib to render headless intraday charts for every stock, locking the Y-axis to a 0% baseline to standardize geometric visual interpretation.

### Phase 3: The Multi-Agent AI Think-Tank
* **`08.0_field_reporter.py`**: A multithreaded asynchronous process using **Qwen-VL** (Vision-Language Model). It "looks" at all 2,500+ generated charts and translates the visual geometry into a dense, 4-sentence quantitative text overview.
* **`09.0_materiality_filter.py`**: The Junior Analyst (**DeepSeek V4**). Reads the 2,500 visual overviews and fundamentally filters out boring "Market Beta" noise, retaining only the mathematically significant, idiosyncratic anomalies.
* **`10.0_editor_in_chief.py`**: The Senior Editor (**GLM 5.2**). Ingests the filtered anomalies, synthesizes a high-level macroeconomic narrative, and ruthlessly curates the absolute Top 20 most explosive movers of the day. **Crucially, it pings a Serverless Upstash Redis database to track a 7-day rolling memory of "Frequent Flyer" anomalies.**

### Phase 4: Output Generation
* **`11.0_generate_newsletter.py`**: Wraps the final AI-curated JSON payload into a clean, email-safe HTML report, dynamically appending interactive 5-Day Yahoo Finance Chart and Stock News links. It also displays a "Frequent Flyer" badge for stocks experiencing extreme volatility multiple times within a 7-day window.

---

## ⚙️ Environment & Execution

### Setup Requirements
You will need an `.env` file in the root directory containing your API credentials and Redis Memory variables:
* `GEMINI_API_KEY` (Google)
* `OPENROUTER_API_KEY` (Qwen-VL routing)
* `DEEPSEEK_API_KEY` (Direct DeepSeek API)
* `ZAI_API_KEY` (Direct GLM 5.2 access via Z.ai)
* `UPSTASH_REDIS_REST_URL` (Serverless Redis Memory)
* `UPSTASH_REDIS_REST_TOKEN` (Serverless Redis Memory)

**Required Python Libraries:**
```bash
pip install selenium bs4 yfinance pandas matplotlib python-dotenv openai google-genai pandas_market_calendars upstash-redis
```

### Execution Strategy & Cost Optimization
To execute the entire pipeline from end to end:
```bash
python 00_execute_pipeline.py
```

**Cron Scheduling Recommendation:**
If automating this pipeline via GitHub Actions or a local cron job, schedule the trigger for **after 4:00 AM Mountain Standard Time (MST)** / **10:00 AM UTC**, Tuesday through Saturday. 

This specifically places the heavy AI lifting (Scripts 08 through 10) outside of DeepSeek's peak surge pricing window (6:00 AM - 10:00 AM UTC), ensuring the pipeline operates at maximum cost efficiency while guaranteeing the prior day's market data is fully settled.