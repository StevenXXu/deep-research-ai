import os
import requests
import json

def scrape_with_firecrawl(url):
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return None
    
    print(f"[Firecrawl] Engaging Heavy Scraper for {url}...", flush=True)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        # Wait 2 seconds to let React/Vue hydration finish
        "actions": [
            {"type": "wait", "milliseconds": 2000}
        ]
    }
    try:
        response = requests.post("https://api.firecrawl.dev/v1/scrape", headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                markdown = data.get("data", {}).get("markdown", "")
                return markdown
        else:
            print(f"[Firecrawl] Error: {response.status_code} {response.text}", flush=True)
    except Exception as e:
        print(f"[Firecrawl] Exception scraping {url}: {e}", flush=True)
    return None

def map_website(url, search_query="about company team leadership product solutions who-we-are"):
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return None
    
    print(f"[Firecrawl] Mapping {url} with semantic search: '{search_query}'...", flush=True)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "search": search_query,
        "limit": 100
    }
    try:
        response = requests.post("https://api.firecrawl.dev/v2/map", headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") or data.get("status") == "success":
                links = data.get("links", [])
                extracted = []
                for link in links:
                    if isinstance(link, dict) and link.get("url"):
                        extracted.append(link.get("url"))
                    elif isinstance(link, str):
                        extracted.append(link)
                return extracted
        else:
            print(f"[Firecrawl] Map Error: {response.status_code} {response.text}", flush=True)
    except Exception as e:
        print(f"[Firecrawl] Map Exception for {url}: {e}", flush=True)
    return None
