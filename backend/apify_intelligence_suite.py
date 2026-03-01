import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
if not APIFY_TOKEN:
    print("Error: APIFY_TOKEN not found.")
    # We don't exit here to allow import without crashing, but methods will fail/warn.

# --- ACTOR CONFIGURATION ---

# 1. Website Content Crawler (ID: aYG0l9s7dbB7j3gbS)
# Documentation: https://apify.com/apify/website-content-crawler
RAG_BROWSER_ACTOR = "aYG0l9s7dbB7j3gbS"
RAG_BROWSER_URL = f"https://api.apify.com/v2/acts/{RAG_BROWSER_ACTOR}/runs?waitForFinish=120"

# 2. LinkedIn Scraper (ID: consummate_mandala/linkedin-company-scraper)
LINKEDIN_ACTOR = "consummate_mandala/linkedin-company-scraper"
LINKEDIN_RUN_URL = f"https://api.apify.com/v2/acts/{LINKEDIN_ACTOR}/runs?waitForFinish=120"

# 3. Reddit Scraper (ID: FgJtjDwJCLhRH9saM)
# Documentation: https://apify.com/trudax/reddit-scraper
REDDIT_ACTOR = "FgJtjDwJCLhRH9saM"
REDDIT_RUN_URL = f"https://api.apify.com/v2/acts/{REDDIT_ACTOR}/runs?waitForFinish=120"


def _run_actor(run_url, payload, label="Actor"):
    """Helper to run an Apify actor and fetch results"""
    if not APIFY_TOKEN:
        print(f"[WARN] Skipping {label}: No APIFY_TOKEN")
        return []
        
    print(f"[APIFY] Launching {label}...")
    try:
        # 1. Start Run
        response = requests.post(
            run_url,
            headers={"Authorization": f"Bearer {APIFY_TOKEN}", "Content-Type": "application/json"},
            json=payload,
            timeout=130 # Slightly longer than wait param
        )
        response.raise_for_status()
        run_data = response.json()['data']
        dataset_id = run_data['defaultDatasetId']
        
        # 2. Fetch Results
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&format=json"
        data_response = requests.get(dataset_url, headers={"Authorization": f"Bearer {APIFY_TOKEN}"})
        data_response.raise_for_status()
        
        items = data_response.json()
        print(f"[APIFY] {label}: Fetched {len(items)} items.")
        return items
    except Exception as e:
        print(f"[ERROR] {label} Error: {e}")
        return []

def scrape_website_content(url):
    """
    Uses Apify Website Content Crawler (aYG0l9s7dbB7j3gbS) to extract clean Markdown.
    """
    # Website Content Crawler uses 'startUrls'
    payload = {
        "startUrls": [{"url": url}],
        "maxCrawlDepth": 1,
        "maxCrawlPages": 5,
        "saveMarkdown": True,
        "proxyConfiguration": {"useApifyProxy": True}
    }
    
    items = _run_actor(RAG_BROWSER_URL, payload, label="Website Crawler")
    
    results = []
    for item in items:
        # Crawler returns 'text' or 'markdown'
        markdown = item.get("markdown") or item.get("text")
        if markdown:
            results.append({
                "title": item.get("metadata", {}).get("title", "Official Site Page"),
                "url": item.get("url", url),
                "content": markdown[:6000],
                "source": "Official Website (Deep Crawl)"
            })
    return results

def scrape_linkedin_company(linkedin_url):
    """
    Scrapes structured data from a LinkedIn Company Page.
    Requires a direct URL (e.g., https://www.linkedin.com/company/openai).
    """
    if "linkedin.com/company" not in linkedin_url:
        print(f"⚠️  Invalid LinkedIn URL provided: {linkedin_url}")
        return []

    payload = {
        "companyUrls": [linkedin_url],
        "maxPosts": 5 # Limit posts to save cost/time
    }
    
    items = _run_actor(LINKEDIN_RUN_URL, payload, label="LinkedIn Scraper")
    return items

def scrape_reddit_search(query):
    """
    Searches Reddit for brand sentiment/discussions.
    """
    payload = {
        "searches": [query],
        "maxItems": 10,
        "sort": "relevance",
        "time": "all"
    }
    
    # Reddit scraper returns flat items usually
    return _run_actor(REDDIT_RUN_URL, payload, label="Reddit Scraper")

if __name__ == "__main__":
    # Test
    print("Testing Apify Module...")
    # res = scrape_website_content("https://www.example.com")
    # print(res)
