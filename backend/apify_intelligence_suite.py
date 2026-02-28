import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
if not APIFY_TOKEN:
    print("Error: APIFY_TOKEN not found.")
    exit(1)

# LinkedIn Company Scraper (Free Tier compatible if available, or lightweight profile scraper)
# Using: 'linkedin-company-scraper' (vanity) or specific ID
# NOTE: LinkedIn scraping is high-risk/expensive. We use a safe, pay-per-result actor if possible.
# Actor: 'curious_coder/linkedin-company-scraper' or similar. 
# For prototype, we'll use a reliable one: "dev_fusion/linkedin-company-scraper" or generic wrapper.
# Let's use a known reliable one for "Company Data".
ACTOR_ID = "kfiW6xK8x7" # Placeholder ID for a generic LinkedIn Scraper, will resolve dynamically if needed.
# Actually, let's use the one we found in search: "scraper-engine/linkedin-company-scraper" 
ACTOR_NAME = "scraper-engine/linkedin-company-employees-scraper"

RUN_URL = f"https://api.apify.com/v2/acts/{ACTOR_NAME}/runs?waitForFinish=120"

def scrape_linkedin_company(company_url):
    print(f"🚀 Launching LinkedIn Scraper for: {company_url}...")
    payload = {
        "startUrls": [{"url": company_url}],
        "maxItems": 20 # Limit to save credits
    }
    
    try:
        response = requests.post(
            RUN_URL,
            headers={"Authorization": f"Bearer {APIFY_TOKEN}", "Content-Type": "application/json"},
            json=payload
        )
        response.raise_for_status()
        run_data = response.json()['data']
        dataset_id = run_data['defaultDatasetId']
        
        # Fetch Results
        DATASET_URL = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&format=json"
        data_response = requests.get(DATASET_URL, headers={"Authorization": f"Bearer {APIFY_TOKEN}"})
        data_response.raise_for_status()
        
        items = data_response.json()
        print(f"✅ Fetched {len(items)} LinkedIn records.")
        return items
    except Exception as e:
        print(f"❌ LinkedIn Scraper Error: {e}")
        return []

def scrape_reddit_search(query):
    print(f"🚀 Launching Reddit Scraper for: {query}...")
    # Actor: 'trudax/reddit-scraper'
    REDDIT_ACTOR = "trudax/reddit-scraper"
    REDDIT_URL = f"https://api.apify.com/v2/acts/{REDDIT_ACTOR}/runs?waitForFinish=120"
    
    payload = {
        "searches": [query],
        "maxItems": 10,
        "sort": "relevance",
        "time": "all"
    }
    
    try:
        response = requests.post(
            REDDIT_URL,
            headers={"Authorization": f"Bearer {APIFY_TOKEN}", "Content-Type": "application/json"},
            json=payload
        )
        response.raise_for_status()
        run_data = response.json()['data']
        dataset_id = run_data['defaultDatasetId']
        
        DATASET_URL = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&format=json"
        data_response = requests.get(DATASET_URL, headers={"Authorization": f"Bearer {APIFY_TOKEN}"})
        data_response.raise_for_status()
        
        items = data_response.json()
        print(f"✅ Fetched {len(items)} Reddit threads.")
        return items
    except Exception as e:
        print(f"❌ Reddit Scraper Error: {e}")
        return []

if __name__ == "__main__":
    # Example Usage
    company = "Voqo AI"
    # linkedin_data = scrape_linkedin_company("https://www.linkedin.com/company/voqo-ai")
    reddit_data = scrape_reddit_search(company)
    
    # Save for inspection
    os.makedirs("memory/data_lake/intelligence", exist_ok=True)
    with open(f"memory/data_lake/intelligence/{company.replace(' ', '_')}_reddit.json", "w") as f:
        json.dump(reddit_data, f, indent=2)
