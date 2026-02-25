import os
import sys
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from exa_py import Exa
from duckduckgo_search import DDGS

# --- SETUP ---
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(root_dir)

from llm_gateway import gateway
import discord_connector as dc

load_dotenv(os.path.join(root_dir, ".env"))

EXA_KEY = os.getenv("EXA_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
BRAVE_KEY = os.getenv("BRAVE_API_KEY")

class ResearchEngine:
    def __init__(self, target_url, document_content=None):
        self.url = target_url
        self.domain = target_url.split("//")[-1].split("/")[0]
        self.company = self.domain.split(".")[0].capitalize()
        self.sources = [] 
        self.questions = [] 
        self.document_content = document_content # New: Uploaded Deck

    def log(self, msg):
        print(f"[RESEARCH] {msg}")
        dc.post("cipher", "PROGRESS", msg)

    # --- SEARCH ENGINES ---
    
    def search_exa(self, query, num=3):
        if not EXA_KEY: return []
        try:
            exa = Exa(EXA_KEY)
            res = exa.search_and_contents(query, type="neural", num_results=num, text=True)
            return [{"title": r.title, "url": r.url, "content": r.text[:1000], "source": "Exa"} for r in res.results]
        except Exception as e:
            self.log(f"Exa Error: {e}")
            return []

    def search_tavily(self, query, num=3):
        if not TAVILY_KEY: return []
        try:
            url = "https://api.tavily.com/search"
            payload = {"api_key": TAVILY_KEY, "query": query, "search_depth": "advanced", "max_results": num}
            res = requests.post(url, json=payload, timeout=10)
            data = res.json()
            return [{"title": r['title'], "url": r['url'], "content": r['content'][:1000], "source": "Tavily"} for r in data.get('results', [])]
        except Exception as e:
            self.log(f"Tavily Error: {e}")
            return []
            
    def search_brave(self, query, num=3):
        if not BRAVE_KEY: return []
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {"X-Subscription-Token": BRAVE_KEY}
            params = {"q": query, "count": num}
            res = requests.get(url, headers=headers, params=params, timeout=10)
            data = res.json()
            # Brave structure varies, assume 'web' -> 'results'
            return [{"title": r['title'], "url": r['url'], "content": r.get('description', '')[:500], "source": "Brave"} for r in data.get('web', {}).get('results', [])]
        except Exception as e:
            self.log(f"Brave Error: {e}")
            return []
            
    def search_ddg(self, query, num=3):
        # Free Fallback
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num))
                return [{"title": r['title'], "url": r['href'], "content": r['body'][:500], "source": "DDG"} for r in results]
        except Exception as e:
            self.log(f"DDG Error: {e}")
            return []

    # --- PHASES ---

    def phase_1_broad_scan(self):
        self.log(f"Phase 1: Broad Scan for '{self.company}'...")

        # Optional uploaded deck/document as primary source
        if self.document_content:
            self.sources.append({
                "title": "Uploaded Document",
                "url": "local-upload",
                "content": self.document_content[:6000],
                "source": "Upload"
            })
        
        # 1. Company General
        q1 = f"{self.company} {self.domain} startup funding news"
        self.sources.extend(self.search_exa(q1, 4))
        self.sources.extend(self.search_tavily(q1, 3))
        
        # 2. Competitors
        q2 = f"{self.company} competitors alternatives market share"
        self.sources.extend(self.search_exa(q2, 4))
        
        # 3. Reviews / Issues
        q3 = f"{self.company} reviews complaints pricing scam"
        self.sources.extend(self.search_tavily(q3, 3) or self.search_ddg(q3, 3))
        
        self.log(f"Found {len(self.sources)} initial sources.")

    def phase_2_gap_analysis(self):
        self.log("Phase 2: Identifying Knowledge Gaps...")
        
        # Summarize current knowledge for LLM
        context = "\n".join([f"- {s['title']} ({s['source']}): {s['content'][:200]}..." for s in self.sources])
        
        prompt = f"""
        You are a Research Director.
        Target: {self.company} ({self.url})
        
        Current Knowledge:
        {context}
        
        Task: Identify 3 critical missing pieces of information needed for an Investment Memo.
        Examples: "Pricing model is unclear", "No info on founders", "Tech stack unknown".
        
        Output: JSON List of 3 search queries to find this info.
        Example: ["{self.company} pricing tier", "{self.company} founders background", "{self.company} API documentation"]
        """
        
        try:
            resp = gateway.generate(prompt, "Return valid JSON list only.")
            # Clean JSON
            resp = resp.replace("```json", "").replace("```", "").strip()
            self.questions = json.loads(resp)
            self.log(f"Gaps Identified: {self.questions}")
        except Exception as e:
            self.log(f"Gap Analysis Failed: {e}")
            self.questions = [f"{self.company} business model", f"{self.company} technology stack", f"{self.company} user reviews"]

    def phase_3_deep_dive(self):
        self.log("Phase 3: Targeted Deep Dive...")

        for q in self.questions:
            self.sources.extend(self.search_exa(q, 3))
            self.sources.extend(self.search_tavily(q, 3) or self.search_ddg(q, 2))

        # 3B. Technology Deep Dive
        tech_queries = [
            f"{self.company} architecture API documentation github",
            f"{self.company} tech stack llm infrastructure",
            f"{self.company} security compliance SOC2 ISO27001"
        ]
        for q in tech_queries:
            self.sources.extend(self.search_exa(q, 2))
            self.sources.extend(self.search_tavily(q, 2) or self.search_ddg(q, 2))

        # 3C. Market/Competition Data Deep Dive
        market_queries = [
            f"{self.company} pricing plans comparison",
            f"{self.company} market size TAM SAM SOM",
            f"{self.company} competitors pricing crunchbase g2"
        ]
        for q in market_queries:
            self.sources.extend(self.search_exa(q, 2))
            self.sources.extend(self.search_tavily(q, 2) or self.search_ddg(q, 2))
            
        self.log(f"Total Sources: {len(self.sources)}")

    def phase_4_synthesis(self):
        self.log("Phase 4: Writing 2000+ Word Report...")
        
        # Deduplicate sources by URL
        seen_urls = set()
        unique_sources = []
        for s in self.sources:
            if s['url'] not in seen_urls:
                unique_sources.append(s)
                seen_urls.add(s['url'])
        
        # Create Citation Map
        citations = []
        context_blob = ""
        for i, s in enumerate(unique_sources):
            ref = f"[{i+1}]"
            citations.append(f"{ref} {s['title']} - {s['url']}")
            context_blob += f"Source {ref}: {s['content']}\n\n"
            
        prompt = f"""
        You are a Senior Investment Analyst.
        Target: {self.company} ({self.url})
        
        Research Data:
        {context_blob}
        
        Task: Write a comprehensive Investment Memo (Minimum 2000 words).
        Style: Professional, Objective, Thorough. Use Markdown.
        
        Requirements:
        1. **Executive Summary** (SWOT Analysis, Key Verdict)
        2. **Product Deep Dive** (Features, Tech Stack, UX)
        3. **Market Landscape** (Competitor Table - compare features/pricing)
        4. **Business Model** (Revenue Streams, Pricing Strategy)
        5. **Traction & Risks** (Funding, Traffic, Legal/Reg Risks)
        6. **Founding Team** (Backgrounds, Track Record)
        7. **Data Consistency Check** (Deck vs. Web Reality - Flag discrepancies)
        8. **Strategic Conclusion** (Buy/Sell/Wait)
        
        **FORMATTING RULES:**
        - **NO CHATTY INTROS:** Do NOT say "Here is the report" or "Okay I will do that". Start directly with the Report Title (# Project Name).
        - Use standard Markdown tables for SWOT and Competitors.
        - **IMPORTANT:** Ensure tables start on a new line and are NOT indented.
        - Example Table:
          | Feature | Company A | Company B |
          | :--- | :--- | :--- |
          | Price | $10 | $20 |
        
        - Use citations like [1], [2] linked to the References.
        """
        
        report = gateway.generate(prompt, "You are a thoughtful analyst. Output ONLY the report.")
        
        # Append References if LLM missed them (safety net)
        if "## References" not in report:
            report += "\n\n## References\n" + "\n".join(citations)
            
        return report

    def run(self):
        self.phase_1_broad_scan()
        self.phase_2_gap_analysis()
        self.phase_3_deep_dive()
        return self.phase_4_synthesis()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        engine = ResearchEngine(sys.argv[1])
        report = engine.run()
        print(report)
    else:
        print("Usage: python research_engine.py <url>")
