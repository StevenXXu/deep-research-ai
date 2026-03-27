import os
import requests
from dotenv import load_dotenv

load_dotenv()

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")

def search_company_by_domain(domain: str) -> dict:
    """
    Search Apollo.io for a company using its domain.
    Returns the best matching company profile or an empty dict if not found.
    """
    if not APOLLO_API_KEY:
        print("[APOLLO] Error: APOLLO_API_KEY not set.")
        return {}

    clean_domain = domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    if not clean_domain:
        return {}

    url = "https://api.apollo.io/v1/organizations/enrich"
    
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json"
    }
    
    payload = {
        "api_key": APOLLO_API_KEY,
        "domain": clean_domain
    }

    try:
        print(f"[APOLLO] Searching for domain: {clean_domain}...")
        response = requests.get(url, headers=headers, params=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data and "organization" in data:
                return data["organization"]
            print("[APOLLO] Domain found, but organization data missing.")
            return {}
        else:
            print(f"[APOLLO] API Error: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        print(f"[APOLLO] Request Failed: {e}")
        return {}

def extract_company_facts(domain: str) -> dict:
    """
    Given a domain, fetches the company from Apollo.io and extracts 
    core facts into a flat dictionary.
    """
    raw_data = search_company_by_domain(domain)
    if not raw_data:
        return {}

    # Extract meaningful fields matching old Coresignal structure
    facts = {
        "true_name": raw_data.get("name", ""),
        "industry": raw_data.get("industry", ""),
        "employees_count": raw_data.get("estimated_num_employees", ""),
        "founded_year": raw_data.get("founded_year", ""),
        "headquarters": raw_data.get("country", ""),
        "description": raw_data.get("short_description", "") or raw_data.get("seo_description", ""),
        "linkedin_url": raw_data.get("linkedin_url", "") 
    }
    
    return {k: v for k, v in facts.items() if v}

def extract_key_executives(company_name: str, domain: str) -> list:
    """
    Waterfall strategy: Try Apollo first, fallback to Exa.
    Replaces Coresignal's extract_key_executives.
    """
    if not APOLLO_API_KEY or not domain:
        return _fallback_to_exa(company_name)

    clean_domain = domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    url = "https://api.apollo.io/v1/mixed_people/search"
    
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json"
    }
    
    payload = {
        "api_key": APOLLO_API_KEY,
        "q_organization_domains": clean_domain,
        "person_titles": ["founder", "co-founder", "ceo", "chief executive officer", "cto", "chief technology officer", "president"],
        "page": 1,
        "per_page": 5
    }

    try:
        print(f"[APOLLO] Searching for key executives at {clean_domain}...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            executives = []
            
            for person in data.get("people", [])[:5]:
                name = person.get("name", "")
                title = person.get("title", "")
                linkedin_url = person.get("linkedin_url", "")
                
                if name and title:
                    executives.append({
                        "name": name,
                        "title": title,
                        "linkedin_url": linkedin_url
                    })
            
            if executives:
                print(f"[APOLLO] Found {len(executives)} executives: {[e['name'] for e in executives]}")
                return executives
            else:
                print("[APOLLO] No key executives found matching titles.")
                return _fallback_to_exa(company_name)
        else:
            print(f"[APOLLO] API Error: {response.status_code} - {response.text}")
            return _fallback_to_exa(company_name)
    except Exception as e:
        print(f"[APOLLO] Request Failed: {e}")
        return _fallback_to_exa(company_name)

def _fallback_to_exa(company_name: str) -> list:
    if not EXA_API_KEY or not company_name:
        return []

    from exa_py import Exa
    
    try:
        print(f"[EXA] Neural searching LinkedIn for founders of {company_name}...")
        exa = Exa(EXA_API_KEY)
        
        query = f"Here is the LinkedIn profile of the founder or CEO of {company_name}:"
        
        results = exa.search_and_contents(
            query,
            num_results=3,
            include_domains=["linkedin.com"],
            text=True
        )
        
        executives = []
        for res in results.results:
            url = res.url
            title = res.title or ""
            
            name_part = title.split("-")[0].split("|")[0].strip()
            
            if "/in/" in url and len(name_part) > 2 and name_part.lower() not in company_name.lower():
                executives.append({
                    "name": name_part,
                    "title": "Founder/CEO (Inferred)",
                    "linkedin_url": url
                })
                
        if executives:
            print(f"[EXA] Found {len(executives)} potential profiles: {[e['name'] for e in executives]}")
        else:
            print("[EXA] No clear founder profiles found.")
            
        return executives
        
    except Exception as e:
        print(f"[EXA] Request Failed: {e}")
        return []
