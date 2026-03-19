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
            print(f"[CORESIGNAL] Debug Response Type: {type(data)}")
            
            result = None
            # If we got hits, return the first one
            if isinstance(data, list) and len(data) > 0:
                # Some coresignal endpoints return list directly for es_dsl depending on version
                result = data[0]
            elif isinstance(data, dict):
                # Standard elasticsearch format
                hits = data.get("hits", {})
                if isinstance(hits, dict):
                    inner_hits = hits.get("hits", [])
                    if isinstance(inner_hits, list) and inner_hits:
                        result = inner_hits[0].get("_source", inner_hits[0])
                elif isinstance(hits, list) and hits:
                     result = hits[0]
                
                if not result:
                    # Direct items format
                    items = data.get("items", [])
                    if isinstance(items, list) and items:
                        result = items[0]
                
                if not result:
                    # Sometimes it just returns a list directly under data
                    if "name" in data:
                        result = data
            
            if isinstance(result, dict):
                return result
            else:
                print(f"[CORESIGNAL] Invalid data format or no match found: {str(data)[:200]}")
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
    
    if not isinstance(raw_data, dict) or not raw_data:
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

def extract_key_executives(company_name: str, domain: str) -> list:
    """
    Search Coresignal for key executives (Founder, CEO, CTO, etc.) of the company.
    """
    if not CORESIGNAL_API_KEY or not company_name:
        return []

    url = f"{BASE_URL}/member_base/search/es_dsl"
    
    headers = {
        "accept": "application/json",
        "apikey": CORESIGNAL_API_KEY,
        "Content-Type": "application/json"
    }

    clean_domain = domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")

    # Query for members currently at this company with executive titles
    payload = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": [
                                { "match": { "experience_company_name": company_name } },
                                { "match": { "experience_company_website": clean_domain } }
                            ],
                            "minimum_should_match": 1
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                { "match": { "title": "founder" } },
                                { "match": { "title": "co-founder" } },
                                { "match": { "title": "ceo" } },
                                { "match": { "title": "chief executive officer" } },
                                { "match": { "title": "cto" } },
                                { "match": { "title": "chief technology officer" } }
                            ],
                            "minimum_should_match": 1
                        }
                    }
                ]
            }
        }
    }

    try:
        print(f"[CORESIGNAL] Searching for key executives at {company_name}...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            executives = []
            
            hits = []
            if isinstance(data, list):
                hits = data
            elif isinstance(data, dict):
                inner_hits = data.get("hits", {})
                if isinstance(inner_hits, dict):
                    hits = inner_hits.get("hits", [])
                elif isinstance(inner_hits, list):
                    hits = inner_hits
                if not hits:
                    hits = data.get("items", [])

            for hit in hits[:5]:
                source = hit.get("_source", hit) if isinstance(hit, dict) else hit
                if source and isinstance(source, dict):
                    name = source.get("name", "")
                    title = source.get("title", "")
                    summary = source.get("summary", "")
                    linkedin_url = source.get("url", "")
                    
                    if name and title:
                        summary_str = summary[:200] + "..." if summary and len(summary) > 200 else summary
                        executives.append({
                            "name": name,
                            "title": title,
                            "summary": summary_str,
                            "linkedin_url": linkedin_url
                        })
            
            print(f"[CORESIGNAL] Found {len(executives)} key executives.")
            return executives
        else:
            print(f"[CORESIGNAL] Exec API Error: {response.status_code} - {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"[CORESIGNAL] Exec Request Exception: {str(e)}")
        return []
