import os
import sys
import json
import time
import requests
import re
import warnings
from datetime import datetime
from dotenv import load_dotenv
from exa_py import Exa
from duckduckgo_search import DDGS
import apify_bridge as apify # Updated: Use new Bridge

# Filter specific warning from duckduckgo_search
warnings.filterwarnings("ignore", category=RuntimeWarning, module="duckduckgo_search")

# --- SETUP ---
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
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
        self.ddg_retries = 0  # Global counter for DDG fallbacks
        
        # Handle 'www.' prefix or subdomains to get proper company name
        domain_parts = self.domain.split('.')
        if domain_parts[0] == 'www' and len(domain_parts) > 2:
            self.company = domain_parts[1].capitalize()
        else:
            self.company = domain_parts[0].capitalize()
            
        self.sources = []  
        self.questions = [] 
        self.document_content = document_content # New: Uploaded Deck

    def log(self, msg):
        print(f"[RESEARCH] {msg}")
        dc.post("cipher", "PROGRESS", msg)

    # --- METADATA & COST ---

    def calculate_cost(self):
        # 1. Exa Cost: $0.001 per search (Neural)
        # Assuming search_exa called N times, num results = avg 3
        # Exa is roughly $10/1000 searches.
        exa_calls = 0 # Need to track this
        # Tavily: Free tier generous, then $0.00x
        # Apify: $5/month platform fee + usage. Reddit Actor is cheap.
        # LLM: Gemini Pro is currently free preview or cheap.
        
        # For now, return a placeholder estimate logic
        # We need to implement counters in the search functions first.
        return 0.15 # Hardcoded estimate for MVP

    def extract_metadata(self, report_text):
        # Use LLM to extract structured data from the generated report
        prompt = f"""
        Extract the following metadata from this report as JSON:
        1. Company Name (Clean string)
        2. Sector Tags (Array of strings, e.g. ["AI", "Fintech"])
        3. Funding Stage (e.g. "Seed", "Series A", "Public", "Unknown")
        
        Report:
        {report_text[:3000]}...
        """
        try:
            resp = gateway.generate(prompt, "Return valid JSON only.")
            if not resp: return {}
            return json.loads(resp.replace("```json", "").replace("```", "").strip())
        except:
            return {"company_name": self.company, "sector_tags": []}
    
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
        # Global limit to prevent infinite loops / stalling
        if self.ddg_retries > 3:
            self.log(f"DDG Search Skipped (Global Limit Reached) for: {query}")
            return []
            
        self.ddg_retries += 1
        
        # Free Fallback
        try:
            # Sleep to prevent rate limiting
            time.sleep(2)
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num))
                return [{"title": r['title'], "url": r['href'], "content": r['body'][:500], "source": "DDG"} for r in results]
        except Exception as e:
            self.log(f"DDG Error: {e}")
            return []

    def _find_linkedin_url(self):
        """Helper: Scan sources for a LinkedIn Company URL"""
        li_pattern = re.compile(r"https?://(www\.)?linkedin\.com/company/[\w-]+")
        
        # 1. Check existing sources
        for s in self.sources:
            match = li_pattern.search(s.get('url', ''))
            if match:
                return match.group(0)
        
        # 2. Targeted search if not found
        self.log(f"LinkedIn URL not found in initial scan. Searching...")
        # Use Brave instead of DDG for this critical search if available
        results = self.search_brave(f"site:linkedin.com/company {self.company} official", num=1)
        if not results:
             results = self.search_ddg(f"site:linkedin.com/company {self.company} official", num=1)
             
        if results:
            match = li_pattern.search(results[0].get('url', ''))
            if match:
                return match.group(0)
        
        return None

    # --- PHASES ---

    def phase_1_broad_scan(self):
        self.log(f"Phase 1: Broad Scan for '{self.company}'...")

        # A. Official Site Deep Extract (Apify)
        try:
            site_data = apify.scrape_website_content(self.url)
            self.sources.extend(site_data)
            self.log(f"Apify: Extracted {len(site_data)} pages from official site.")
        except Exception as e:
            self.log(f"Apify Site Crawl Error: {e}")

        # B. Uploaded Doc
        if self.document_content:
            self.sources.append({
                "title": "Uploaded Document",
                "url": "local-upload",
                "content": self.document_content[:6000],
                "source": "Upload"
            })
        
        # 1. Company General
        q1 = f"{self.company} {self.domain} startup funding news"
        # Try Exa first
        res = self.search_exa(q1, 4)
        if not res: res = self.search_tavily(q1, 3)
        self.sources.extend(res)
        
        # 2. Competitors
        q2 = f"{self.company} competitors alternatives market share"
        self.sources.extend(self.search_exa(q2, 4))
        
        # 3. Reviews / Issues
        q3 = f"{self.company} reviews complaints pricing scam"
        res = self.search_tavily(q3, 3)
        if not res: res = self.search_ddg(q3, 3)
        self.sources.extend(res)
        
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
            if not resp:
                resp = "[]"
            # Clean JSON
            resp = resp.replace("```json", "").replace("```", "").strip()
            self.questions = json.loads(resp)
            self.log(f"Gaps Identified: {self.questions}")
        except Exception as e:
            self.log(f"Gap Analysis Failed: {e}")
            self.questions = [f"{self.company} business model", f"{self.company} technology stack", f"{self.company} user reviews"]

    def phase_3_deep_dive(self):
        self.log("Phase 3: Targeted Deep Dive...")

        # 3A. Apify Intelligence (Social & LinkedIn)
        try:
            self.log(f"Phase 3A: Apify Scanning (Reddit & LinkedIn) for {self.company}...")
            
            # 1. Reddit Sentiment (Brand Search)
            reddit_data = apify.scrape_reddit_search(self.company)
            for item in reddit_data:
                self.sources.append({
                    "title": item.get('title'),
                    "url": item.get('url'),
                    "content": f"[Reddit Sentiment] {item.get('description') or item.get('title') or item.get('snippet')}",
                    "source": "Reddit (Apify)"
                })
            
            # 2. LinkedIn Data (Structured Company Data)
            linkedin_url = self._find_linkedin_url()
            if linkedin_url:
                self.log(f"Found LinkedIn URL: {linkedin_url}. Scraping...")
                li_data = apify.scrape_linkedin_company(linkedin_url)
                if li_data:
                    # Usually returns a list of 1 company profile
                    profile = li_data[0]
                    # Format as a source
                    content_str = (
                        f"Name: {profile.get('name')}\n"
                        f"Followers: {profile.get('followerCount')}\n"
                        f"Description: {profile.get('description')}\n"
                        f"Employees: {profile.get('employeeCount', 'N/A')}\n"
                        f"Industry: {profile.get('industry')}\n"
                        f"Website: {profile.get('websiteUrl')}"
                    )
                    self.sources.append({
                        "title": f"LinkedIn Profile: {profile.get('name')}",
                        "url": linkedin_url,
                        "content": f"[LinkedIn Official Data]\n{content_str}",
                        "source": "LinkedIn (Apify)"
                    })
            else:
                self.log("Could not find LinkedIn URL. Skipping deep LinkedIn scrape.")

        except Exception as e:
            self.log(f"Apify Module Warning: {e}")

        # 3B. Market Momentum (Google Trends)
        try:
            self.log(f"Phase 3B: Checking Market Momentum...")
            trends_data = apify.scrape_google_trends(self.company)
            self.sources.extend(trends_data)
        except Exception as e:
            self.log(f"Trends Warning: {e}")

        # 3C. Tech & Market Gaps
        for q in self.questions:
            self.sources.extend(self.search_exa(q, 3))
            self.sources.extend(self.search_tavily(q, 3) or self.search_ddg(q, 2))

        # 3C. Standard Deep Dive (Tech + Market)
        tech_queries = [
            f"{self.company} architecture API documentation github",
            f"{self.company} tech stack llm infrastructure",
            f"{self.company} security compliance SOC2 ISO27001"
        ]
        for q in tech_queries:
            self.sources.extend(self.search_exa(q, 2))
            
        market_queries = [
            f"{self.company} pricing plans comparison",
            f"{self.company} market size TAM SAM SOM",
            f"{self.company} competitors pricing crunchbase g2"
        ]
        for q in market_queries:
            self.sources.extend(self.search_tavily(q, 2) or self.search_ddg(q, 2))
            
        self.log(f"Total Sources: {len(self.sources)}")

    def phase_audit_consistency(self):
        """Phase 3.5: Audit sources for identity mismatch (e.g. wrong company with same name)"""
        self.log("Phase 3.5: Auditing Sources for Consistency...")
        
        # Prepare context for LLM Audit
        # We limit to title/url/snippet to save context window
        source_list = []
        for i, s in enumerate(self.sources):
            source_list.append(f"ID {i}: Title='{s.get('title')}' URL='{s.get('url')}' Snippet='{s.get('content', '')[:200]}'")
        
        audit_prompt = f"""
        You are a QA Lead Auditor.
        Target Company: {self.company}
        Target URL: {self.url}
        
        Task: Review the list of gathered sources. Identify any source that clearly refers to a DIFFERENT company (e.g. same name but wrong industry/country).
        
        Sources:
        {json.dumps(source_list, indent=2)}
        
        Output JSON ONLY:
        {{
            "exclude_ids": [integer indices of bad sources],
            "reason": "Brief explanation of why"
        }}
        If all look correct, return {{ "exclude_ids": [], "reason": "All clear" }}.
        """
        
        try:
            resp = gateway.generate(audit_prompt, "Return valid JSON only.")
            if not resp:
                resp = "{}"
            # Clean JSON
            resp = resp.replace("```json", "").replace("```", "").strip()
            audit_result = json.loads(resp)
            
            exclude_ids = audit_result.get("exclude_ids", [])
            if exclude_ids:
                self.log(f"AUDIT ALERT: Excluding {len(exclude_ids)} bad sources. Reason: {audit_result.get('reason')}")
                # Filter sources
                self.sources = [s for i, s in enumerate(self.sources) if i not in exclude_ids]
            else:
                self.log("Audit Passed: No identity conflicts detected.")
                
        except Exception as e:
            self.log(f"Audit Warning: Failed to run consistency check. {e}")

    def phase_4_synthesis(self):
        self.log("Phase 4: Writing 2000+ Word Report...")
        
        # Deduplicate sources by URL
        seen_urls = set()
        unique_sources = []
        for s in self.sources:
            if s.get('url') and s['url'] not in seen_urls:
                unique_sources.append(s)
                seen_urls.add(s['url'])
        
        # Create Citation Map (Markdown Links)
        citations = []
        context_blob = ""
        for i, s in enumerate(unique_sources):
            ref_num = i + 1
            # Hyperlink Format: [1] [Title](URL)
            # Safe title handling
            raw_title = s.get('title')
            if not raw_title:
                raw_title = 'Unknown Source'
            title = str(raw_title).replace('[', '(').replace(']', ')')
            
            url = s.get('url', '#')
            citations.append(f"[{ref_num}] [{title}]({url})")
            
            # Safe content handling
            content = s.get('content') or ''
            context_blob += f"Source [{ref_num}]: {str(content)[:2000]}\n\n"
            
        prompt = f"""
        You are a Senior Investment Analyst.
        Target: {self.company} ({self.url})
        
        Research Data:
        {context_blob}
        
        Task: Write a comprehensive Investment Memo (Minimum 2000 words).
        Style: Professional, Objective, Thorough. Use Markdown.
        
        **CRITICAL SAFETY & STYLE RULES:**
        1. **OBJECTIVE FACTS ONLY:** Do NOT provide "Recommendations", "Verdicts", "Next Steps", or "Advice". Do not say "Wait and observe", "Buy", or "Sell". Your job is data aggregation, not consulting.
        2. **NO 'SCAM' ACCUSATIONS:** Unless proven by government/major news, assume innocence. Label issues as "User Controversy".
        3. **NO REFERENCES SECTION:** Do NOT write a References/Sources section at the end. The system appends this automatically.
        4. **NO NUMBERED HEADERS:** Do NOT number the sections (e.g. use "Executive Summary", NOT "1. Executive Summary").
        5. **MANDATORY TABLES:** 
           - SWOT Analysis MUST be a Markdown table.
           - Market Landscape MUST be a Markdown table.
        
        Requirements:
        1. **Executive Summary** (Include SWOT Analysis as a Table)
        2. **Product Deep Dive** (Features, Tech Stack, UX)
        3. **Market Landscape** (Competitor Table - columns: Competitor, Features, Pricing)
        4. **Social Sentiment & Risk** (Reddit/User Feedback - Highlight "Real" sentiment vs PR)
        5. **Business Model** (Revenue Streams, Pricing Strategy)
        6. **Traction & Risks** (Funding, Traffic, Legal/Reg Risks)
        7. **Founding Team** (Backgrounds, Track Record - Check LinkedIn signals)
        8. **Data Consistency Check** (Deck vs. Web Reality - Flag discrepancies)
        
        **FORMATTING RULES:**
        - **NO CHATTY INTROS:** Start directly with the Report Title (# Project Name).
        - **IMPORTANT:** Ensure all tables are preceded by an empty line.
        - Use citations like [1], [2] in the text.
        """
        
        report = gateway.generate(prompt, "You are a thoughtful analyst. Output ONLY the report.")
        
        if not report:
            self.log("Error: LLM returned None for report generation.")
            return "# Analysis Failed\n\nDeep Research collected relevant sources, but the LLM failed to synthesize the final report due to a timeout or safety filter.\n\n## Data gathered\n" + f"{len(unique_sources)} sources found."

        # FORCE APPEND REFERENCES (Programmatic, Clickable)
        # We strip any LLM-hallucinated references first to avoid duplicates
        if "## References" in report:
            report = report.split("## References")[0].strip()
            
        report += "\n\n## References\n"
        for c in citations:
            report += f"- {c}\n"
            
        return report

    def run(self):
        self.phase_1_broad_scan()
        self.phase_2_gap_analysis()
        self.phase_3_deep_dive()
        self.phase_audit_consistency() # New Audit Step
        return self.phase_4_synthesis()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        engine = ResearchEngine(sys.argv[1])
        report = engine.run()
        print(report)
    else:
        print("Usage: python research_engine.py <url>")
