import os
import requests
import logging

XCRAWL_API_KEY = os.getenv("XCRAWL_API_KEY")
BASE_URL = "https://run.xcrawl.com/v1"

def _headers():
    return {
        "Authorization": f"Bearer {XCRAWL_API_KEY}",
        "Content-Type": "application/json"
    }

def scrape_url(url: str) -> dict:
    if not XCRAWL_API_KEY:
        raise Exception("XCRAWL_API_KEY not set")
    
    payload = {
        "url": url,
        "mode": "sync",
        "js_render": {"enabled": True, "wait_until": "networkidle"},
        "output": {"formats": ["markdown"]}
    }
    
    res = requests.post(f"{BASE_URL}/scrape", json=payload, headers=_headers(), timeout=45)
    if res.status_code == 200:
        data = res.json().get("data", {})
        return {
            "url": url,
            "title": data.get("metadata", {}).get("title", ""),
            "content": data.get("markdown", "") or "",
            "source": "xCrawl"
        }
    else:
        raise Exception(f"xCrawl Scrape API Error: {res.status_code} - {res.text}")

def map_site(url: str, limit: int = 100) -> list:
    if not XCRAWL_API_KEY:
        raise Exception("XCRAWL_API_KEY not set")
        
    payload = {
        "url": url,
        "limit": limit,
        "include_subdomains": False
    }
    
    res = requests.post(f"{BASE_URL}/map", json=payload, headers=_headers(), timeout=45)
    if res.status_code == 200:
        data = res.json().get("data", {})
        return data.get("links", [])
    else:
        raise Exception(f"xCrawl Map API Error: {res.status_code} - {res.text}")

