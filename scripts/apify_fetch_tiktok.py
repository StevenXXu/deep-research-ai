import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
if not APIFY_TOKEN:
    print("Error: APIFY_TOKEN not found.")
    exit(1)

# Actor: clockworks/tiktok-scraper
# Task: Scrape hashtag #AI
ACTOR_ID = "GdWCkxBtKWOsKjdch"
RUN_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?waitForFinish=120"

payload = {
    "hashtags": ["AI"],
    "resultsPerPage": 10,
    "shouldDownloadVideos": False,
    "shouldDownloadCovers": False,
    "shouldDownloadSlideshowImages": False,
    "searchSection": ""
}

print(f"🚀 Launching Apify Actor: {ACTOR_ID}...")

try:
    response = requests.post(
        RUN_URL,
        headers={"Authorization": f"Bearer {APIFY_TOKEN}", "Content-Type": "application/json"},
        json=payload
    )
    response.raise_for_status()
    run_data = response.json()['data']
    
    dataset_id = run_data['defaultDatasetId']
    print(f"✅ Run Succeeded! Dataset ID: {dataset_id}")

    # Fetch Results
    DATASET_URL = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&format=json"
    data_response = requests.get(DATASET_URL, headers={"Authorization": f"Bearer {APIFY_TOKEN}"})
    data_response.raise_for_status()
    
    items = data_response.json()
    print(f"📊 Fetched {len(items)} items.")
    
    # Save to file
    os.makedirs("memory/data_lake/tiktok", exist_ok=True)
    with open("memory/data_lake/tiktok/trending_ai.json", "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
        
    print("💾 Data saved to memory/data_lake/tiktok/trending_ai.json")

except Exception as e:
    print(f"❌ Error: {e}")
    if hasattr(e, 'response') and e.response:
        print(e.response.text)
