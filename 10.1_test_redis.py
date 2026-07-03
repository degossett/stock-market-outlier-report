import os
from dotenv import load_dotenv
from upstash_redis import Redis

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

print(">>> Testing Upstash Redis Connection...")

try:
    # Connect to the cloud database
    redis = Redis(
        url=os.getenv("UPSTASH_REDIS_REST_URL"), 
        token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
    )
    
    # Write a test memory, read it back, then delete it
    redis.set("system_check", "Connection successful! Database is online.")
    memory = redis.get("system_check")
    
    print(f"✅ SUCCESS: {memory}")
    
    redis.delete("system_check")
    
except Exception as e:
    print(f"❌ ERROR: Could not connect to Upstash. Check your .env file.\nDetails: {e}")