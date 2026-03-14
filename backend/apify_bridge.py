import os
import json
import subprocess
from typing import Optional
from dotenv import load_dotenv

from scraper_config import ScraperConfig, DEFAULT_CONFIG

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

def scrape_website_content(url: str, scraper_config: Optional[ScraperConfig] = None):
    """Replaces old 'scrape_website_content' using 'apify-ultimate-scraper'"""
    if not APIFY_TOKEN:
        print("[Apify Bridge] Missing APIFY_TOKEN. Cannot run crawler.", flush=True)
        return []

    config = scraper_config or DEFAULT_CONFIG

    print(
        f"[Apify Bridge] Scraping {url} via Ultimate Scraper (proxy={'on' if config.proxy_url else 'off'})...",
        flush=True,
    )

    from apify_client import ApifyClient

    client = ApifyClient(APIFY_TOKEN)

    base_run_input = {
        "startUrls": [{"url": url}],
        "maxCrawlPages": 5,
        "crawlerType": "playwright:firefox",
        "proxyConfiguration": {"useApifyProxy": True},
        "useBuilder": "latest",
        "removeElementsCssSelector": "nav, footer, script, style, noscript, svg, img, iframe, iframe, header, aside",
    }
    run_input = config.to_apify_run_input(base_run_input)

    try:
        # Actor: apify/website-content-crawler (The "Ultimate" one for text)
        print("[Apify Bridge] Invoking Actor with Playwright & JS Rendering...", flush=True)
        run = client.actor("apify/website-content-crawler").call(
            run_input=run_input, timeout_secs=240, memory_mbytes=4096
        )
        print("[Apify Bridge] Actor Finished. Fetching results...", flush=True)

        # Fetch results
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items(limit=20).items

        results = []
        for item in dataset_items:
            results.append(
                {
                    "title": item.get("metadata", {}).get("title") or item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("markdown") or item.get("text"),
                    "source": "Apify",
                }
            )
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

def scrape_crunchbase(query):
    """Bridge for 'epctex/crunchbase-scraper' to fetch funding data"""
    print(f"[Apify Bridge] Scraping Crunchbase for '{query}'...", flush=True)
    from apify_client import ApifyClient
    client = ApifyClient(APIFY_TOKEN)

    # Actor: epctex/crunchbase-scraper (A popular crunchbase actor)
    run_input = {
        "search": query,
        "mode": "organizations",
        "maxItems": 1
    }

    try:
        print(f"[Apify Bridge] Invoking Crunchbase Actor...", flush=True)
        # Fast timeout since we only need the top result
        run = client.actor("epctex/crunchbase-scraper").call(run_input=run_input, timeout_secs=60, memory_mbytes=1024)
        print(f"[Apify Bridge] Crunchbase Actor Finished.", flush=True)
        
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items(limit=1).items
        
        if not dataset_items:
            return []
            
        company_data = dataset_items[0]
        
        # Extract critical funding data
        funding_rounds = company_data.get('funding_rounds', [])
        total_funding = company_data.get('total_funding_amount', 'Unknown')
        last_funding_type = company_data.get('last_funding_type', 'Unknown')
        
        # Build a tight summary for the LLM
        summary = f"Total Funding: {total_funding}. Last Round: {last_funding_type}. "
        if funding_rounds:
            summary += "Recent Rounds: "
            for r in funding_rounds[:3]: # Top 3 recent
                amt = r.get('money_raised', 'Undisclosed')
                date = r.get('announced_on', 'Unknown date')
                investors = ", ".join([i.get('investor_name', '') for i in r.get('investors', [])[:2]])
                summary += f"[{r.get('funding_type', 'Round')} in {date}: {amt} (Investors: {investors})] "
                
        return [{
            "title": f"Crunchbase: {company_data.get('name', query)}",
            "url": company_data.get('url', 'https://crunchbase.com'),
            "content": f"[FUNDING & VALUATION DATA] {summary}",
            "source": "Crunchbase (Apify)"
        }]
        
    except Exception as e:
        print(f"[Bridge Error - Crunchbase] {e}", flush=True)
        return []

def scrape_linkedin_company(linkedin_url):
    """Bridge for 'consummate_mandala/linkedin-company-scraper' or similar"""
    print(f"[Apify Bridge] Scraping LinkedIn: {linkedin_url}...", flush=True)
    from apify_client import ApifyClient
    client = ApifyClient(APIFY_TOKEN)

    # Actor: consummate_mandala/linkedin-company-scraper
    run_input = {
        "companyUrls": [linkedin_url],
        "maxPosts": 0, # We just want the company profile info, not posts
        "scrapeAbout": True,
        "scrapeEmployees": True
    }

    try:
        print(f"[Apify Bridge] Invoking LinkedIn Actor...", flush=True)
        run = client.actor("consummate_mandala/linkedin-company-scraper").call(run_input=run_input, timeout_secs=90, memory_mbytes=1024)
        print(f"[Apify Bridge] LinkedIn Actor Finished.", flush=True)
        
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items(limit=1).items
        
        if not dataset_items:
            return []
            
        company_data = dataset_items[0]
        
        # Extract 'About Us' and founder info
        about = company_data.get('about', '')
        tagline = company_data.get('tagline', '')
        employee_count = company_data.get('employeeCount', 'Unknown')
        
        # Build summary
        summary = f"Tagline: {tagline}\nCompany Size: {employee_count} employees on LinkedIn\nAbout: {about[:1000]}"
        
        return [{
            "title": f"LinkedIn Company Profile: {company_data.get('name', 'Unknown')}",
            "url": linkedin_url,
            "content": f"[LINKEDIN ABOUT & TEAM DATA] {summary}",
            "source": "LinkedIn (Apify)"
        }]
        
    except Exception as e:
        print(f"[Bridge Error - LinkedIn] {e}", flush=True)
        return []
