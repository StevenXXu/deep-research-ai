import os
import sys
import json
import asyncio
import aiohttp
from typing import List, Dict, Any
from urllib.parse import urlparse
from apify_module import ApifyIntelligence

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)

# Configuration
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")

class MetaSearchAgent:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.seen_urls = set()
        self.apify = ApifyIntelligence()

    async def search_brave(self, query: str, session: aiohttp.ClientSession) -> List[Dict]:
        """Broad search using Brave API"""
        if not BRAVE_API_KEY:
            print("[WARN] BRAVE_API_KEY missing. Skipping Brave.")
            return []
            
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"X-Subscription-Token": BRAVE_API_KEY, "Accept": "application/json"}
        params = {"q": query, "count": 5}
        
        try:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for item in data.get('web', {}).get('results', []):
                        results.append({
                            "source": "Brave (Broad)",
                            "title": item.get('title'),
                            "url": item.get('url'),
                            "snippet": item.get('description'),
                            "published": item.get('age', '')
                        })
                    return results
                else:
                    print(f"[ERROR] Brave API error: {resp.status}")
        except Exception as e:
            print(f"[ERROR] Brave search failed: {e}")
        return []

    async def search_tavily(self, query: str, session: aiohttp.ClientSession) -> List[Dict]:
        """Real-time news search using Tavily API"""
        if not TAVILY_API_KEY:
            print("[WARN] TAVILY_API_KEY missing. Skipping Tavily.")
            return []

        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced", # advanced gives better snippets
            "include_domains": [],
            "exclude_domains": [],
            "max_results": 5
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for item in data.get('results', []):
                        results.append({
                            "source": "Tavily (Real-time)",
                            "title": item.get('title'),
                            "url": item.get('url'),
                            "snippet": item.get('content'),
                            "published": "" # Tavily doesn't always return published date in standard format
                        })
                    return results
                else:
                    print(f"[ERROR] Tavily API error: {resp.status}")
        except Exception as e:
            print(f"[ERROR] Tavily search failed: {e}")
        return []

    async def search_exa(self, query: str, session: aiohttp.ClientSession) -> List[Dict]:
        """Deep semantic search using Exa (Metaphor) API"""
        if not EXA_API_KEY:
            print("[WARN] EXA_API_KEY missing. Skipping Exa.")
            return []

        # Exa endpoint for search
        url = "https://api.exa.ai/search"
        headers = {
            "x-api-key": EXA_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "numResults": 5,
            "useAutoprompt": True, # Let Exa optimize the query for semantic search
            "contents": {"text": True} # Get content snippets
        }

        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for item in data.get('results', []):
                        results.append({
                            "source": "Exa (Semantic)",
                            "title": item.get('title') or "Untitled",
                            "url": item.get('url'),
                            "snippet": item.get('text', '')[:300] + "...", # Truncate long text
                            "published": item.get('publishedDate', '')
                        })
                    return results
                else:
                    print(f"[ERROR] Exa API error: {resp.status}")
        except Exception as e:
            print(f"[ERROR] Exa search failed: {e}")
        return []

    def deduplicate(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate URLs and merge sources"""
        unique_results = []
        url_map = {}

        for item in results:
            url = item.get('url')
            if not url:
                continue
            
            # Simple normalization
            parsed = urlparse(url)
            norm_url = f"{parsed.netloc}{parsed.path}"

            if norm_url in url_map:
                # Merge source info if already exists
                existing = url_map[norm_url]
                if item['source'] not in existing['source']:
                    existing['source'] += f", {item['source']}"
            else:
                url_map[norm_url] = item
                unique_results.append(item)
        
        return unique_results

    async def run(self, query: str):
        print(f"[Deep Dive] Launching search for: '{query}'...")
        
        async with aiohttp.ClientSession() as session:
            # Run all searches in parallel
            tasks = [
                self.search_brave(query, session),
                self.search_tavily(query, session),
                self.search_exa(query, session),
                self.apify.scrape_reddit_sentiment(query)
            ]
            
            # Gather results
            all_results_lists = await asyncio.gather(*tasks)
            
            # Flatten list
            flat_results = [item for sublist in all_results_lists for item in sublist]
            
            # Deduplicate
            final_results = self.deduplicate(flat_results)
            
            # Output as JSON for the Analyst to consume
            print(json.dumps(final_results, indent=2, ensure_ascii=True))
            
            # Generate a brief summary for logging
            print(f"\n[DONE] Scan Complete. Found {len(final_results)} unique sources from Brave, Tavily, and Exa.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python research_agent.py <query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    agent = MetaSearchAgent()
    asyncio.run(agent.run(query))
