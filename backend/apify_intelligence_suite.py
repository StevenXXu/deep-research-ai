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

# 1. RAG Web Browser (For deep website content extraction)
# Great for turning a URL into LLM-ready Markdown
RAG_BROWSER_ACTOR = "apify/rag-web-browser"
RAG_BROWSER_URL = f"https://api.apify.com/v2/acts/{RAG_BROWSER_ACTOR}/runs?waitForFinish=120"

# 2. LinkedIn Scraper
# Using a specific actor for company data. 
# Note: 'scraper-engine/linkedin-company-employees-scraper' is one option.
LINKEDIN_ACTOR = "scraper-engine/linkedin-company-employees-scraper"
LINKEDIN_RUN_URL = f"https://api.apify.com/v2/acts/{LINKEDIN_ACTOR}/runs?waitForFinish=120"

# 3. Reddit Scraper
REDDIT_ACTOR = "trudax/reddit-scraper"
REDDIT_RUN_URL = f"https://api.apify.com/v2/acts/{REDDIT_ACTOR}/runs?waitForFinish=120"


def _run_actor(run_url, payload, label="Actor"):
    """Helper to run an Apify actor and fetch results"""
    if not APIFY_TOKEN:
        print(f"⚠️  Skipping {label}: No APIFY_TOKEN")
        return []
        
    print(f"🚀 Launching {label}...")
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
        print(f"✅ {label}: Fetched {len(items)} items.")
        return items
    except Exception as e:
        print(f"❌ {label} Error: {e}")
        return []

def scrape_website_content(url):
    """
    Uses Apify RAG Web Browser to crawl the target site and extract clean Markdown.
    Best for getting the 'official' truth from the company's own pages.
    """
    payload = {
        "startUrls": [{"url": url}],
        "maxDepth": 1, # Keep shallow for speed/cost (Home + 1 click)
        "maxPagesPerCrawl": 5, # Limit pages to avoid huge bills
        "returnMarkdown": True,
        "returnHtml": False,
        "proxyConfiguration": {"useApifyProxy": True}
    }
    
    items = _run_actor(RAG_BROWSER_URL, payload, label="Website Crawler (RAG)")
    
    results = []
    for item in items:
        # Extract markdown content
        markdown = item.get("markdown", "")
        if markdown:
            results.append({
                "title": item.get("metadata", {}).get("title", "Official Site Page"),
                "url": item.get("url", url),
                "content": markdown[:3000], # Truncate for context window safety
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
        "startUrls": [{"url": linkedin_url}],
        "maxItems": 1 # We just need the main company profile
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
