import os
import requests
import json
import asyncio
from typing import List, Dict, Any

# Configuration
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

class ApifyIntelligence:
    def __init__(self):
        self.enabled = bool(APIFY_TOKEN)
        if not self.enabled:
            print("[WARN] APIFY_TOKEN missing. Apify Intelligence disabled.")

    async def scrape_linkedin_company(self, query: str) -> List[Dict]:
        """Use Apify to find and scrape LinkedIn company data"""
        if not self.enabled: return []
        
        print(f"[Apify] Scouting LinkedIn for: {query}...")
        # Note: In a real scenario, we'd first search for the LinkedIn URL via Brave/Google
        # For V4 prototype, we assume we might get a URL or we skip this step if no URL is readily available
        # OR we use a Google Search Scraper on Apify to find the LinkedIn URL first.
        
        # Simplified: We will return a placeholder or use the 'google-search-scraper' on Apify if we want to be fancy.
        # But to keep it fast, let's just skip the complex URL discovery for now unless we pass a URL.
        return []

    async def scrape_reddit_sentiment(self, query: str) -> List[Dict]:
        """Use Apify to scrape Reddit discussions"""
        if not self.enabled: return []
        
        print(f"[Apify] Listening to Reddit for: {query}...")
        
        # Actor: trudax/reddit-scraper
        ACTOR_ID = "trudax/reddit-scraper" 
        RUN_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?waitForFinish=120"
        
        payload = {
            "searches": [query],
            "maxItems": 5,
            "sort": "relevance",
            "time": "all"
        }
        
        # We wrap the synchronous requests in asyncio.to_thread to not block the event loop
        try:
            return await asyncio.to_thread(self._run_actor, RUN_URL, payload, "Reddit")
        except Exception as e:
            print(f"[ERROR] Apify Reddit scan failed: {e}")
            return []

    def _run_actor(self, run_url: str, payload: Dict, source_name: str) -> List[Dict]:
        headers = {
            "Authorization": f"Bearer {APIFY_TOKEN}", 
            "Content-Type": "application/json"
        }
        
        resp = requests.post(run_url, headers=headers, json=payload)
        resp.raise_for_status()
        run_data = resp.json()['data']
        dataset_id = run_data['defaultDatasetId']
        
        # Fetch results
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&format=json"
        data_resp = requests.get(dataset_url, headers={"Authorization": f"Bearer {APIFY_TOKEN}"})
        data_resp.raise_for_status()
        
        items = data_resp.json()
        results = []
        for item in items:
            # Normalize Reddit data
            if source_name == "Reddit":
                results.append({
                    "source": "Reddit (Social Sentiment)",
                    "title": item.get('title') or item.get('body', '')[:50],
                    "url": item.get('url'),
                    "snippet": item.get('body') or item.get('selftext') or "",
                    "published": item.get('created_at', '')
                })
        return results
