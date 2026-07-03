import os
import json
import time
import base64
import threading
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

IMAGE_DIR = os.path.join(BASE_DIR, "vlm_individual_charts")
OUTPUT_JSON = os.path.join(BASE_DIR, "qwen_visual_overviews.json")

# Initialize OpenRouter Client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Using the massive 235B Instruct model
VISION_MODEL = "qwen/qwen3.7-plus"

# --- CONCURRENCY CONTROLS ---
MAX_WORKERS = 2  # Safe, stealthy speed limit for overnight processing
file_lock = threading.Lock() # Protects our JSON file from corruption

def encode_image_to_base64(image_path):
    """Reads a physical image from the hard drive and converts it to a Base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_visual_overview(base64_image):
    """Sends the Base64 chart to Qwen-VL and extracts the 4-sentence overview."""
    
    # Highly specific "Decoder Ring" prompt for the blank chart
    prompt = (
        "You are an elite quantitative analyst. Look at this normalized 5-minute interval line chart "
        "for a single U.S. stock's most recent trading session. "
        "CRITICAL CHART SCALE RULES: "
        "- The left edge of the image is the 9:30 AM Open. The right edge is the 4:00 PM Close. "
        "- The red dashed line represents a 0% price change from yesterday's close. "
        "- The absolute top edge of the image mathematically represents exactly +15%. "
        "- The absolute bottom edge of the image mathematically represents exactly -15%. "
        "- If the black line touches or breaks through the top or bottom of the image, the stock exceeded a 15% move. "
        "Based entirely on your internal training knowledge of equity markets, price action, and volatility, "
        "write a concise, exactly 4-sentence analytical overview of this stock's intraday behavior. "
        "Do not include any fluff or conversational filler."
    )
    
    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.2 
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"      [!] API Error: {e}")
        return None

def process_single_chart(ticker, image_path, overviews):
    """Worker function to process one image, handle retries, and thread-safe save."""
    img_base64 = encode_image_to_base64(image_path)
    
    overview_text = None
    max_retries = 4
    
    # Exponential Backoff loop for handling rate limits (429s) gracefully
    for attempt in range(max_retries):
        overview_text = get_visual_overview(img_base64)
        if overview_text:
            break
            
        sleep_time = 2 ** attempt
        print(f"      [~] {ticker} hit a snag. Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time) 
        
    if overview_text:
        # Thread-safe write to the JSON file using the Lock
        with file_lock:
            overviews[ticker] = overview_text
            with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
                json.dump(overviews, f, indent=4)
        return ticker, True
        
    return ticker, False

def run_field_reporter():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Step 09.0: The Field Reporter (OpenRouter Qwen 235B)...")
    
    if not os.path.exists(IMAGE_DIR):
        print(f"⚠️ Image directory missing at {IMAGE_DIR}. Run Script 08 first.")
        return
        
    all_files = [f for f in os.listdir(IMAGE_DIR) if f.endswith('.png')]
    if not all_files:
        print("⚠️ No images found in the directory!")
        return
        
    overviews = {}
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
            try:
                overviews = json.load(f)
                print(f">>> Found {len(overviews)} existing overviews. Resuming...")
            except json.JSONDecodeError:
                pass
            
    unprocessed_files = [f for f in all_files if f.replace('.png', '') not in overviews]
    
    if not unprocessed_files:
        print(">>> All charts have been analyzed by the Field Reporter! Exiting.")
        return
        
    print(f">>> Processing {len(unprocessed_files)} charts using {MAX_WORKERS} concurrent workers...")

    # Start the Thread Pool
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        # Submit all images to the worker pool
        future_to_ticker = {
            executor.submit(process_single_chart, filename.replace('.png', ''), os.path.join(IMAGE_DIR, filename), overviews): filename 
            for filename in unprocessed_files
        }
        
        # Monitor as they complete
        completed = 0
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future].replace('.png', '')
            try:
                _, success = future.result()
                completed += 1
                status = "✅" if success else "❌"
                print(f"  ... [{completed}/{len(unprocessed_files)}] {status} {ticker}")
            except Exception as exc:
                print(f"  ❌ {ticker} generated a critical worker exception: {exc}")
                
    print(f"\n✅ Success! All visual overviews saved to: {OUTPUT_JSON}")

if __name__ == '__main__':
    run_field_reporter()