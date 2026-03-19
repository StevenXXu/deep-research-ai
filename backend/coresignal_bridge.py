import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

CORESIGNAL_API_KEY = os.getenv("CORESIGNAL_API_KEY")
BASE_URL = "https://api.coresignal.com/cdapi/v2"

def search_company_by_domain(domain: str) -> dict:
    """
    Search Coresignal for a company using its domain name via Elasticsearch DSL.
    Returns the best matching company profile or an empty dict if not found.
    """
    if not CORESIGNAL_API_KEY:
        print("[CORESIGNAL] Error: CORESIGNAL_API_KEY not set.")
        return {}

    # Clean domain (remove http/https/www)
    clean_domain = domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    if not clean_domain:
        return {}

    url = f"{BASE_URL}/company_base/search/es_dsl"
    
    headers = {
        "accept": "application/json",
        "apikey": CORESIGNAL_API_KEY,
        "Content-Type": "application/json"
    }

    # Elasticsearch DSL query to find the company by website
    payload = {
        "query": {
            "bool": {
                "should": [
                    { "match": { "website": clean_domain } },
                    { "wildcard": { "website": f"*{clean_domain}*" } }
                ],
                "minimum_should_match": 1
            }
        }
    }

    try:
        print(f"[CORESIGNAL] Searching for domain: {clean_domain}...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # If we got hits, return the first one
            if isinstance(data, list) and len(data) > 0:
                # Some coresignal endpoints return list directly for es_dsl depending on version
                return data[0]
            elif isinstance(data, dict):
                # Standard elasticsearch format
                hits = data.get("hits", {}).get("hits", [])
                if hits:
                    return hits[0].get("_source", hits[0])
                # Direct items format
                items = data.get("items", [])
                if items:
                    return items[0]
                # Sometimes it just returns a list directly under data
                if data and "name" in data:
                    return data
            
            print(f"[CORESIGNAL] No matching company found for {clean_domain}.")
            return {}
        else:
            print(f"[CORESIGNAL] API Error: {response.status_code} - {response.text}")
            return {}
            
    except Exception as e:
        print(f"[CORESIGNAL] Request Exception: {str(e)}")
        return {}

def extract_company_facts(domain: str) -> dict:
    """
    High-level function to get clean company facts for the Research Engine.
    """
    raw_data = search_company_by_domain(domain)
    
    if not raw_data:
        return {}

    # Extract meaningful fields
    facts = {
        "true_name": raw_data.get("name", ""),
        "industry": raw_data.get("industry", ""),
        "employees_count": raw_data.get("employees_count", ""),
        "founded_year": raw_data.get("founded_year", ""),
        "headquarters": raw_data.get("headquarters_country", ""),
        "description": raw_data.get("description", ""),
        "linkedin_url": raw_data.get("url", "") # Coresignal usually stores the LinkedIn URL here
    }
    
    # Filter out empty keys
    return {k: v for k, v in facts.items() if v}
