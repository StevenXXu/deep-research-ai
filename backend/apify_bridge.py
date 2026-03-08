import os
import json
import subprocess
from dotenv import load_dotenv

# Load Env for APIFY_TOKEN
load_dotenv()
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

# Skill Paths
SKILLS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../skills/apify-agent-skills/skills'))

def run_node_script(script_path, payload):
    """Executes a Node.js skill script with JSON payload via stdin."""
    if not APIFY_TOKEN:
        print("[ERROR] APIFY_TOKEN is missing.", flush=True)
        return None

    env = os.environ.copy()
    env["APIFY_TOKEN"] = APIFY_TOKEN
    
    try:
        pass
    except Exception as e:
        print(f"[ERROR] Node Execution Failed: {e}", flush=True)
        return None

# --- IMPLEMENTATION ---

def scrape_website_content(url):
    """Replaces old 'scrape_website_content' using 'apify-ultimate-scraper'"""
    print(f"[Apify Bridge] Scraping {url} via Ultimate Scraper...", flush=True)
    
    from apify_client import ApifyClient
    client = ApifyClient(APIFY_TOKEN)
    
    run_input = {
        "startUrls": [{"url": url}],
        "maxCrawlPages": 5, # Limit for speed
        "crawlerType": "cheerio", # Use lighter cheerio to prevent memory issues
        "proxyConfiguration": {"useApifyProxy": True}
    }
    
    try:
        # Actor: apify/website-content-crawler (The "Ultimate" one for text)
        print(f"[Apify Bridge] Invoking Actor...", flush=True)
        run = client.actor("apify/website-content-crawler").call(run_input=run_input, timeout_secs=180, memory_mbytes=1024)
        print(f"[Apify Bridge] Actor Finished. Fetching results...", flush=True)
        
        # Fetch results
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items(limit=20).items
        
        results = []
        for item in dataset_items:
            results.append({
                "title": item.get("metadata", {}).get("title") or item.get("title"),
                "url": item.get("url"),
                "content": item.get("markdown") or item.get("text"),
                "source": "Apify Ultimate Scraper"
            })
        return results
        
    except Exception as e:
        print(f"[Bridge Error] {e}", flush=True)
        return []

def scrape_reddit_search(query):
    """Replaces old Reddit scraper using 'apify-brand-reputation-monitoring' (Reddit Scraper)"""
    print(f"[Apify Bridge] Searching Reddit for '{query}'...", flush=True)
    from apify_client import ApifyClient
    client = ApifyClient(APIFY_TOKEN)
    
    run_input = {
        "searches": [query],
        "maxItems": 10,
        "sort": "relevance",
        "time": "all"
    }
    
    try:
        # Actor: trudax/reddit-scraper-lite
        print(f"[Apify Bridge] Starting Reddit Actor (timeout=45s)...", flush=True)
        
        # Start asynchronously
        run = client.actor("trudax/reddit-scraper-lite").start(run_input=run_input, timeout_secs=45, memory_mbytes=1024)
        run_id = run["id"]
        default_dataset_id = run["defaultDatasetId"]
        print(f"[Apify Bridge] Reddit Run Started: {run_id}. Waiting for finish...", flush=True)
        
        # Wait for finish
        run_client = client.run(run_id)
        run_info = run_client.wait_for_finish()
        
        status = run_info.get("status")
        if status != "SUCCEEDED":
             print(f"[Apify Bridge] Reddit Run finished with status: {status}. Skipping fetch.", flush=True)
             return []

        print(f"[Apify Bridge] Reddit Run Succeeded. Fetching items...", flush=True)
        
        # Fetch items
        dataset_items = client.dataset(default_dataset_id).list_items(limit=10).items 
        print(f"[Apify Bridge] Fetched {len(dataset_items)} Reddit items.", flush=True)
        
        results = []
        for item in dataset_items:
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "description": item.get("body"),
                "source": "Reddit (Apify)"
            })
        return results
    except Exception as e:
        print(f"[Bridge Error] {e}", flush=True)
        return []

def scrape_google_trends(query):
    """Bridge for 'apify-trend-analysis' (Google Trends)"""
    print(f"[Apify Bridge] Fetching Google Trends for '{query}'...", flush=True)
    from apify_client import ApifyClient
    client = ApifyClient(APIFY_TOKEN)
    
    # Actor: apify/google-trends-scraper
    run_input = {
        "searchTerms": [query],
        "timeRange": "today 5-y", # Last 5 years (fixed from 12-m)
        "geo": "", # Worldwide
        "category": "", # All categories (string)
        "outputAsJson": True
    }
    
    try:
        print(f"[Apify Bridge] Invoking Google Trends Actor...", flush=True)
        # Increased timeout to 90s to handle heavy initial page load
        run = client.actor("apify/google-trends-scraper").call(run_input=run_input, timeout_secs=90, memory_mbytes=1024)
        print(f"[Apify Bridge] Trends Actor Finished.", flush=True)
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items(limit=10).items
        print(f"[Apify Bridge] Fetched Trends Data.", flush=True)
        
        # Format for context
        trends_summary = []
        if dataset_items:
            # Assuming first item has the timeline
            data = dataset_items[0].get('interestOverTime', [])
            if data:
                # Get last 3 months average vs first 3 months
                recent = data[-4:]
                start = data[:4]
                recent_avg = sum([d.get('value', [0])[0] for d in recent]) / len(recent) if recent else 0
                start_avg = sum([d.get('value', [0])[0] for d in start]) / len(start) if start else 0
                
                trend_direction = "Stable"
                if recent_avg > start_avg * 1.2: trend_direction = "Rising 📈"
                if recent_avg < start_avg * 0.8: trend_direction = "Falling 📉"
                
                summary = f"Trend Direction: {trend_direction} (Avg Interest: {int(recent_avg)}/100)"
                trends_summary.append({
                    "title": f"Google Trends: {query}",
                    "url": "https://trends.google.com",
                    "content": summary,
                    "source": "Google Trends (Apify)"
                })
        return trends_summary
        
    except Exception as e:
        print(f"[Bridge Error - Trends] {e}", flush=True)
        return []

def scrape_linkedin_company(linkedin_url):
    """Bridge for 'consummate_mandala/linkedin-company-scraper'"""
    print(f"[Apify Bridge] Scraping LinkedIn: {linkedin_url}...", flush=True)
    from apify_client import ApifyClient
    client = ApifyClient(APIFY_TOKEN)

    # Actor: consummate_mandala/linkedin-company-scraper
    run_input = {
        "companyUrls": [linkedin_url],
        "maxPosts": 5
    }

    try:
        print(f"[Apify Bridge] Invoking LinkedIn Actor...", flush=True)
        run = client.actor("consummate_mandala/linkedin-company-scraper").call(run_input=run_input, timeout_secs=90, memory_mbytes=1024)
        print(f"[Apify Bridge] LinkedIn Actor Finished.", flush=True)
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items(limit=5).items
        
        print(f"[Apify Bridge] Fetched {len(dataset_items)} LinkedIn items.", flush=True)
        return dataset_items
        
    except Exception as e:
        print(f"[Bridge Error - LinkedIn] {e}", flush=True)
        return []
