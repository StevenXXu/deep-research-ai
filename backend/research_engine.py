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
import apify_bridge as apify
from scraper_config import ScraperConfig

# --- SETUP ---
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(root_dir)

from llm_gateway import gateway
# import discord_connector as dc  # Disabled: using Railway logs only

load_dotenv(os.path.join(root_dir, ".env"))

EXA_KEY = os.getenv("EXA_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
BRAVE_KEY = os.getenv("BRAVE_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")


class ResearchEngine:
    def __init__(
        self,
        target_url,
        document_content=None,
        language="English",
        scraper_config: ScraperConfig = None,
    ):
        self.url = target_url
        if target_url.startswith("http://") or target_url.startswith("https://"):
            self.domain = target_url.split("//")[-1].split("/")[0]
        else:
            self.domain = target_url

        self.language = language

        if scraper_config is None:
            scraper_config = ScraperConfig.from_env()
        self.scraper_config = scraper_config

        # Usage Counters (For Costing)
        self.usage = {
            "exa_queries": 0,
            "tavily_queries": 0,
            "apify_runs": 0,
            "llm_input_chars": 0,  # Approx 4 chars = 1 token
            "llm_output_chars": 0,
        }

        # Handle 'www.' prefix or subdomains to get proper company name
        domain_parts = self.domain.split(".")
        if len(domain_parts) > 1:
            if domain_parts[0] == "www" and len(domain_parts) > 2:
                self.company = domain_parts[1].capitalize()
            else:
                self.company = domain_parts[0].capitalize()
        else:
            self.company = self.domain.capitalize()

        self.sources = []
        self.questions = []
        self.document_content = document_content  # New: Uploaded Deck
        self.truth_keywords = []  # NEW: Keywords extracted from official sources to guide filtering

    def log(self, msg):
        print(f"[RESEARCH] {msg}")
        # Discord logging disabled - using Railway logs only

    def calculate_cost(self):
        # Precise Pricing Model (USD)
        RATES = {
            "exa": 0.010,  # $10/1k searches
            "tavily": 0.005,  # $5/1k searches
            "apify": 0.050,  # Est per run (compute units)
            "llm_in": 1.25 / 1_000_000,  # $1.25 per 1M tokens
            "llm_out": 5.00 / 1_000_000,  # $5.00 per 1M tokens
        }

        # Calculate
        input_tokens = self.usage["llm_input_chars"] / 4
        output_tokens = self.usage["llm_output_chars"] / 4

        cost = (
            (self.usage["exa_queries"] * RATES["exa"])
            + (self.usage["tavily_queries"] * RATES["tavily"])
            + (self.usage["apify_runs"] * RATES["apify"])
            + (input_tokens * RATES["llm_in"])
            + (output_tokens * RATES["llm_out"])
        )

        # Add Infrastructure Overhead Estimate (Amortized)
        # E.g. $100 fixed cost / 1000 reports = $0.10 buffer
        overhead = 0.10

        total = cost + overhead
        self.log(
            f"Cost Analysis: API=${cost:.4f} + Fixed=${overhead:.2f} = Total ${total:.4f}"
        )

        return round(total, 4)

    def extract_metadata(self, report_text):
        """
        Uses LLM to structured data from the generated report for the Admin Dashboard.
        """
        prompt = f"""
        Analyze the following investment memo and extract metadata as JSON.

        Memo Excerpt:
        {report_text[:4000]}...

        Output JSON ONLY:
        {{
            "company_name": "Exact Company Name",
            "sector_tags": ["Sector1", "Sector2"],
            "funding_stage": "Seed/Series A/Public/Unknown",
            "risk_score": 1-10
        }}
        """
        try:
            # Re-use gateway. No extra cost for this extraction usually (or minimal)
            resp = gateway.generate(prompt, "Return valid JSON only.")
            if not resp:
                return {}
            # Clean up potential markdown formatting and decode
            clean_resp = resp.replace("```json", "").replace("```", "").strip()

            # Find the first '{' and last '}' to handle LLM preamble/postamble
            start_idx = clean_resp.find("{")
            end_idx = clean_resp.rfind("}")
            if start_idx != -1 and end_idx != -1:
                clean_resp = clean_resp[start_idx : end_idx + 1]

            return json.loads(clean_resp)
        except Exception as e:
            self.log(f"Metadata Extraction Warning: {e}")
            return {"company_name": self.company, "sector_tags": []}

    def search_exa(self, query, num=3):
        if not EXA_KEY:
            return []
        try:
            self.usage["exa_queries"] += 1  # Track Cost
            exa = Exa(EXA_KEY)
            res = exa.search_and_contents(
                query, type="neural", num_results=num, text=True
            )
            return [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.text[:1000],
                    "source": "Exa",
                }
                for r in res.results
            ]
        except Exception as e:
            self.log(f"Exa Error: {e}")
            return []

    def search_tavily(self, query, num=3):
        if not TAVILY_KEY:
            return []
        try:
            self.usage["tavily_queries"] += 1  # Track Cost
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": TAVILY_KEY,
                "query": query,
                "search_depth": "advanced",
                "max_results": num,
            }
            res = requests.post(url, json=payload, timeout=10)
            data = res.json()
            return [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "content": r["content"][:1000],
                    "source": "Tavily",
                }
                for r in data.get("results", [])
            ]
        except Exception as e:
            self.log(f"Tavily Error: {e}")
            return []

    def search_brave(self, query, num=3):
        if not BRAVE_KEY:
            return []
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {"X-Subscription-Token": BRAVE_KEY}
            params = {"q": query, "count": num}
            res = requests.get(url, headers=headers, params=params, timeout=10)
            data = res.json()
            # Brave structure varies, assume 'web' -> 'results'
            return [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "content": r.get("description", "")[:500],
                    "source": "Brave",
                }
                for r in data.get("web", {}).get("results", [])
            ]
        except Exception as e:
            self.log(f"Brave Error: {e}")
            return []

    def search_ddg(self, query, num=3):
        # Replaced DDG with Serper as fallback
        if not SERPER_KEY:
            self.log("Serper API key not set. Skipping fallback search.")
            return []

        self.log(f"Serper Fallback Search: {query}...")

        try:
            import requests
            url = "https://google.serper.dev/search"
            payload = {
                "q": query,
                "num": num
            }
            headers = {
                "X-API-Key": SERPER_KEY,
                "Content-Type": "application/json"
            }
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()

            results = []
            if "organic" in data:
                for r in data.get("organic", [])[:num]:
                    results.append({
                        "title": r.get("title"),
                        "url": r.get("link"),
                        "content": r.get("snippet", "")[:500],
                        "source": "Serper"
                    })
            return results

        except Exception as e:
            self.log(f"Serper Error: {e}")
            return []

    def _find_linkedin_url(self):
        """Helper: Scan sources for a LinkedIn Company URL"""
        li_pattern = re.compile(r"https?://(www\.)?linkedin\.com/company/[\w-]+")

        # 1. Check existing sources
        for s in self.sources:
            match = li_pattern.search(s.get("url", ""))
            if match:
                return match.group(0)

        # 2. Targeted search if not found
        self.log(f"LinkedIn URL not found in initial scan. Searching...")
        # Use Brave instead of DDG for this critical search if available
        results = self.search_brave(
            f"site:linkedin.com/company {self.company} official", num=1
        )
        if not results:
            results = self.search_ddg(
                f"site:linkedin.com/company {self.company} official", num=1
            )

        if results:
            match = li_pattern.search(results[0].get("url", ""))
            if match:
                return match.group(0)

        return None

    # --- PHASES ---

    def phase_1_broad_scan(self):
        self.log(f"Phase 1: Broad Scan for '{self.company}'...")

        # A. Official Site Extract (Scrapling -> Apify Fallback)
        # DISABLED: Evomi removed due to 30s timeout limitation
        import re
        scraper_kwargs = self.scraper_config.to_stealthy_fetcher_kwargs()

        try:
            self.log(
                f"Scrapling: Fetching target site with config: proxy={bool(self.scraper_config.proxy_url)}, UA={self.scraper_config.user_agent[:30]}..."
            )
            from scrapling.fetchers import StealthyFetcher

            # Fetch Home Page with config
            page = StealthyFetcher.fetch(self.url, headless=True, **scraper_kwargs)
            title = page.css("title::text").get() or self.domain

            # Extract readable text
            texts = [t.strip() for t in page.css("body *::text").getall() if t.strip()]
            clean_text = re.sub(r"\s+", " ", " ".join(texts))

            # CF / Anti-bot detection
            if (
                "Just a moment..." in title
                or "Cloudflare" in title
                or len(clean_text) < 50
            ):
                self.log(
                    f"Scrapling: Potential block detected. Title='{title}', Content length={len(clean_text)}"
                )
                raise Exception(
                    "Scrapling hit Cloudflare Challenge or empty DOM. Triggering deep Apify Playwright fallback."
                )

            self.sources.append(
                {
                    "title": title,
                    "url": self.url,
                    "content": clean_text[:6000],
                    "source": "Scrapling (Home Page)",
                }
            )
            self.log(f"Scrapling: Extracted {len(clean_text)} chars from {self.url}")

            # Attempt to fetch deeper core pages (About, Product, Team, etc.)
            links = page.css("a::attr(href)").getall()
            target_links = []

            core_page_keywords = [
                "about",
                "product",
                "service",
                "solution",
                "business",
                "case",
                "tech",
                "contact",
                "team",
                "pricing",
            ]

            for l in set(links):
                if not l:
                    continue
                l_lower = str(l).lower()

                if any(keyword in l_lower for keyword in core_page_keywords):
                    if l.startswith("http") and self.domain in l:
                        target_links.append(l)
                    elif l.startswith("/"):
                        base = self.url.rstrip("/")
                        target_links.append(f"{base}{l}")

            fetched_count = 1

            def score_link(url_str):
                url_str = url_str.lower()
                if "about" in url_str or "team" in url_str:
                    return 3
                if "product" in url_str or "tech" in url_str:
                    return 2
                return 1

            target_links.sort(key=score_link, reverse=True)

            for l in target_links[:4]:
                self.log(f"Scrapling: Following internal link {l}...")
                try:
                    sub_page = StealthyFetcher.fetch(l, headless=True, **scraper_kwargs)
                    sub_title = sub_page.css("title::text").get() or l
                    sub_texts = [
                        t.strip()
                        for t in sub_page.css("body *::text").getall()
                        if t.strip()
                    ]
                    sub_clean_text = re.sub(r"\s+", " ", " ".join(sub_texts))
                    self.sources.append(
                        {
                            "title": sub_title,
                            "url": l,
                            "content": sub_clean_text[:4000],
                            "source": "Scrapling (Subpage)",
                        }
                    )
                    fetched_count += 1
                except Exception as sub_e:
                    self.log(f"Scrapling Subpage Error: {sub_e}")

            self.log(
                f"Scrapling: Extracted {fetched_count} core pages from official site."
            )

        except Exception as e:
            self.log(f"Scrapling Error: {e}")
            self.log("Falling back to Apify Deep Crawl...")
            try:
                site_data = apify.scrape_website_content(
                    self.url, scraper_config=self.scraper_config
                )
                self.sources.extend(site_data)
                self.usage["apify_runs"] += 1
                self.log(f"Apify: Extracted {len(site_data)} pages from official site.")
            except Exception as e2:
                self.log(f"Apify Site Crawl Error: {e2}")

        # B. Uploaded Doc
        if self.document_content:
            self.sources.append(
                {
                    "title": "Uploaded Document",
                    "url": "local-upload",
                    "content": self.document_content[:6000],
                    "source": "Upload",
                }
            )

        # --- ENTITY ANCHORING (Identify True Company Name) ---
        # Instead of trusting the domain name, we ask the LLM to read the official site data.
        official_texts = [
            s["content"][:2000]
            for s in self.sources
            if s["source"] in ["Scrapling (Home Page)", "Scrapling (Subpage)", "Apify", "Upload"]
        ]
        
        if official_texts:
            self.log("Entity Anchoring: Extracting true company identity from official sources...")
            combined_text = "\n".join(official_texts)[:6000]
            entity_prompt = f"""
            Analyze the following text extracted from the official website/document of the domain '{self.domain}'.
            
            Task:
            1. Identify the TRUE, exact name of the company or product. (Sometimes the domain 'wavemotionai.com' belongs to 'WaveForms AI' or 'Vibemotion' belongs to a specific product).
            2. Write a one-sentence description of what they actually do (One-liner).
            
            Output MUST be valid JSON ONLY:
            {{
                "true_company_name": "Exact Name",
                "one_liner": "They build X for Y using Z."
            }}
            
            Text:
            {combined_text}
            """
            try:
                import json
                entity_resp = gateway.generate(entity_prompt, "Return valid JSON only.")
                entity_resp = entity_resp.replace("```json", "").replace("```", "").strip()
                entity_data = json.loads(entity_resp)
                
                true_name = entity_data.get("true_company_name", self.company)
                one_liner = entity_data.get("one_liner", "")
                
                if true_name and len(true_name) > 1 and true_name.lower() != "unknown":
                    self.log(f"Entity Anchored: Domain '{self.domain}' resolved to True Name: '{true_name}'")
                    self.company = true_name  # Update to the real name
                    self.company_one_liner = one_liner
                else:
                    self.company_one_liner = ""
            except Exception as e:
                self.log(f"Entity Anchoring failed: {e}")
                self.company_one_liner = ""
        else:
            self.company_one_liner = ""

        # 1. Company General
        search_target = f"{self.company} ({self.company_one_liner})" if getattr(self, "company_one_liner", "") else f"{self.company} {self.domain}"
        q1 = f"{search_target} startup funding news"
        # Try Exa first
        res = self.search_exa(q1, 4)
        if not res:
            res = self.search_tavily(q1, 3)
        self.sources.extend(res)

        # 2. Competitors
        q2 = f"{search_target} competitors alternatives market share"
        self.sources.extend(self.search_exa(q2, 4))

        # 3. Reviews / Issues
        q3 = f"{self.company} reviews complaints pricing scam"
        res = self.search_tavily(q3, 3)
        if not res:
            res = self.search_ddg(q3, 3)
        self.sources.extend(res)

        self.log(f"Found {len(self.sources)} initial sources.")

    def phase_1_5_rerank_sources(self):
        """Rerank sources to improve quality and reduce noise"""
        if len(self.sources) <= 10:
            self.log(f"Skipping reranking: only {len(self.sources)} sources")
            return
        
        try:
            from reranking_layer import RerankingService
            
            self.log(f"Reranking {len(self.sources)} sources...")
            reranker = RerankingService()
            
            # Build query from company name and domain
            query = f"{self.company} {self.domain} startup company analysis"
            
            # Rerank sources
            reranked = reranker.rerank(
                query=query,
                sources=self.sources,
                top_k=15  # Keep top 15 after reranking
            )
            
            # Log improvement
            original_count = len(self.sources)
            self.sources = reranked
            self.log(f"Reranking: Reduced from {original_count} to {len(self.sources)} high-quality sources")
            
            # Log top sources for debugging
            top_sources = [s.get('source', 'Unknown') for s in self.sources[:5]]
            self.log(f"Top sources: {', '.join(top_sources)}")
            
        except Exception as e:
            self.log(f"Reranking failed (non-critical): {e}")
            # Continue with original sources if reranking fails

    def phase_2_gap_analysis(self):
        self.log("Phase 2: Extracting Ground Truth & Knowledge Gaps...")

        # Summarize ONLY the official sources for truth extraction
        official_sources = [
            s
            for s in self.sources
            if s["source"]
            in ["Scrapling (Home Page)", "Scrapling (Subpage)", "Apify", "Upload"]
        ]
        # Increased context limit to 3000 chars per page to ensure team names and deep tech aren't truncated
        official_context = "\n".join(
            [f"- {s['title']}: {s['content'][:3000]}..." for s in official_sources]
        )

        prompt = f"""
        You are an elite OSINT (Open Source Intelligence) Director analyzing a target company's official materials.
        Target Company: {self.company}
        Target URL: {self.url}

        Official Data (Ground Truth):
        {official_context}

        Task:
        1. Extract the names and exact roles of ALL founders, executives, or key team members mentioned.
        2. Extract exactly 3 highly specific, distinctive technical/industry keywords that uniquely define what this company does. (e.g., if they do Brain-Computer Interfaces using light, use "Optrode", "Photonics", "Neural". Do NOT use generic words like "AI", "Software", "Tech").
        3. Identify 3 critical missing pieces of information needed for a VC Investment Memo (e.g., funding history, direct competitors, real user traction).

        Output MUST be valid JSON ONLY:
        {{
            "founding_team": [{{"name": "John Doe", "role": "CEO"}}, ...],
            "truth_keywords": ["keyword1", "keyword2", "keyword3"],
            "search_queries": ["query 1", "query 2", "query 3"]
        }}
        """

        try:
            resp = gateway.generate(prompt, "Return valid JSON only.")
            if not resp:
                resp = "{}"
            resp = resp.replace("```json", "").replace("```", "").strip()
            data = json.loads(resp)

            self.truth_keywords = [k.lower() for k in data.get("truth_keywords", [])]
            self.questions = data.get(
                "search_queries",
                [
                    f"{self.company} business model",
                    f"{self.company} technology stack",
                    f"{self.company} competitors",
                ],
            )
            self.official_team = data.get(
                "founding_team", []
            )  # NEW: Store official team to bypass hallucinated names later

            self.log(f"Ground Truth Team: {self.official_team}")
            self.log(f"Ground Truth Keywords Locked: {self.truth_keywords}")
            self.log(f"Gaps Identified: {self.questions}")
        except Exception as e:
            self.log(f"Gap Analysis Failed: {e}")
            self.questions = [
                f"{self.company} business model",
                f"{self.company} technology stack",
                f"{self.company} user reviews",
            ]
            self.truth_keywords = []
            self.official_team = []

    def phase_3_deep_dive(self):
        self.log("Phase 3: Targeted Deep Dive...")

        # 3A. Apify Intelligence (Reddit & Crunchbase)
        try:
            self.log(
                f"Phase 3A: Apify Scanning (Reddit & Crunchbase) for {self.company}..."
            )
            self.usage["apify_runs"] += 2  # Track Cost (2 actors)

            # 1. Reddit Sentiment
            reddit_query = f'"{self.company}" (startup OR tech OR software OR business)'
            reddit_data = apify.scrape_reddit_search(reddit_query)
            for item in reddit_data:
                # PHYSICAL FILTER: Drop irrelevant fiction/game noise
                content_lower = (
                    str(item.get("description", "")).lower()
                    + " "
                    + str(item.get("title", "")).lower()
                )
                bad_words = [
                    "novel",
                    "chapter",
                    "fiction",
                    "anime",
                    "book",
                    "manga",
                    "character",
                    "episode",
                    "fantasy",
                    "tbate",
                ]
                if any(bw in content_lower for bw in bad_words):
                    self.log(f"Filtered out Reddit noise: {item.get('title')}")
                    continue

                self.sources.append(
                    {
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "content": f"[Reddit Sentiment] {item.get('description') or item.get('title')}",
                        "source": "Reddit (Apify)",
                    }
                )

            # 2. Crunchbase Funding Data (Replaces Pitchbook API)
            crunchbase_data = apify.scrape_crunchbase(self.company)
            if crunchbase_data:
                self.sources.extend(crunchbase_data)

        except Exception as e:
            self.log(f"Apify Module Warning: {e}")

        # 3B. Founder Detective (NEW)
        self.phase_founder_deep_dive()

        # 3C. Exit Analysis (NEW - Part B)
        self.phase_exit_analysis()

        # 3D. Traffic Reality Check (NEW - Part C)
        self.phase_traffic_check()

        # 3E. Hiring Detective
        self.phase_hiring_detective()

        # 3F. Time Machine
        self.phase_time_machine()

        # 3E. Market Momentum (Google Trends)
        try:
            self.log(f"Phase 3E: Checking Market Momentum...")
            self.usage["apify_runs"] += 1  # Track Cost
            trends_data = apify.scrape_google_trends(self.company)
            self.sources.extend(trends_data)
        except Exception as e:
            self.log(f"Trends Warning: {e}")

        # 3F. Tech & Market Gaps
        for q in self.questions:
            self.sources.extend(self.search_exa(q, 3))
            self.sources.extend(self.search_tavily(q, 3) or self.search_ddg(q, 2))

    def phase_hiring_detective(self):
        """Phase 3E: The Hiring Signal (Job Board Scraper)"""
        self.log("Phase 3E: Hiring Detective (Analyzing Job Boards)...")
        # Search major ATS platforms for active roles to infer company focus
        queries = [
            f"site:jobs.lever.co {self.company}",
            f"site:boards.greenhouse.io {self.company}",
            f"site:jobs.ashbyhq.com {self.company}",
        ]
        hiring_sources = []
        for q in queries:
            res = self.search_ddg(
                q, 2
            )  # Free search is enough for finding job board links
            if res:
                for r in res:
                    r["content"] = "[HIRING SIGNAL DATA] " + r["content"]
                hiring_sources.extend(res)

        if hiring_sources:
            self.sources.extend(hiring_sources)
            self.log(f"Found {len(hiring_sources)} active job board signals.")

    def phase_time_machine(self):
        """Phase 3F: Wayback Machine check for Pivot Alerts"""
        self.log("Phase 3F: Time Machine Audit (Wayback Machine)...")
        try:
            # Call the public Internet Archive API for the closest snapshot from 6-12 months ago
            import datetime
            import requests

            # Target timestamp: 6 months ago
            target_date = (
                datetime.datetime.now() - datetime.timedelta(days=180)
            ).strftime("%Y%md")
            # Wayback Availability API
            url = f"http://archive.org/wayback/available?url={self.domain}&timestamp={target_date}"
            res = requests.get(url, timeout=5).json()

            if res.get("archived_snapshots") and res["archived_snapshots"].get(
                "closest"
            ):
                snapshot = res["archived_snapshots"]["closest"]
                archive_url = snapshot.get("url")
                timestamp = snapshot.get("timestamp")
                if archive_url:
                    self.sources.append(
                        {
                            "title": f"Historical Archive ({timestamp})",
                            "url": archive_url,
                            "content": f"[PIVOT CHECK] Historical website snapshot available at: {archive_url}. The LLM should note if current messaging heavily deviates from past positioning.",
                            "source": "Wayback Machine",
                        }
                    )
                    self.log(f"Found historical snapshot from {timestamp}.")
        except Exception as e:
            self.log(f"Time Machine Warning: {e}")

    def phase_exit_analysis(self):
        """Phase 3C: Research potential exits (M&A, IPO)"""
        self.log("Phase 3C: Exit Analysis & M&A Landscape...")
        # Get sector from LLM context or guess
        # We'll use broad queries to capture the sector automatically
        queries = [
            f"recent acquisitions in {self.company} industry 2024 2025",
            f"who acquires companies like {self.company}",
            f"{self.company} competitors M&A strategy",
            f"top strategic acquirers in {self.company} sector",
        ]
        for q in queries:
            res = self.search_tavily(q, 2)
            # Tag content for LLM
            for r in res:
                r["content"] = "[EXIT/M&A DATA] " + r["content"]
            self.sources.extend(res)

    def phase_traffic_check(self):
        """Phase 3D: Verify traffic claims via SimilarWeb/Semrush public data"""
        self.log("Phase 3D: Traffic Reality Check (Search Hack)...")
        # Strategy 2: Search Hack (As requested by user: site:similarweb.com/website/...)
        queries = [
            f"site:similarweb.com/website/{self.domain} traffic stats",
            f"site:semrush.com/website/{self.domain} traffic analytics",
            f"site:ubersuggest.com/traffic/overview/domain/{self.domain}",
            f"{self.domain} monthly visits worthofweb",
        ]

        # Use Tavily for deeper snippet extraction if possible, else DDG
        for q in queries:
            # Tavily handles "site:" queries reasonably well
            res = self.search_tavily(q, 1)  # Just top 1 is enough usually
            if not res:
                res = self.search_ddg(q, 2)

            if res:
                # Tag these sources for the LLM to notice
                for r in res:
                    # Highlight numbers if possible? No, let LLM do it.
                    r["content"] = "[TRAFFIC DATA (VERIFICATION)] " + r["content"]
                self.sources.extend(res)
                self.log(f"Traffic Check: Found {len(res)} sources for {q}")

    def phase_founder_deep_dive(self):
        """
        Specialized phase to vet the founding team using Ground Truth.
        """
        self.log("Phase 3B: Founder Detective (Vetting Team)...")

        founders = getattr(self, "official_team", [])

        if not founders:
            self.log(
                "No founders found in Official Ground Truth. Attempting precise external extraction..."
            )
            # We ONLY search if we didn't find them on the official site.
            q_init = f'"{self.company}" CEO OR Founder OR CTO'
            init_res = self.search_tavily(q_init, 2)
            self.sources.extend(init_res)

            context = "\n".join(
                [f"- {s['title']}: {s['content'][:200]}..." for s in init_res]
            )
            prompt = f"""
            Extract the names and roles of the key founders/executives of {self.company}.
            CRITICAL: Only extract them if they are explicitly stated to be founders/executives of {self.company}. Do not hallucinate.
            Return JSON list: [{{"name": "Name", "role": "CEO"}}]
            If none found, return [].
            Context:
            {context}
            """
            try:
                resp = gateway.generate(prompt, "Return valid JSON only.")
                if resp:
                    founders = json.loads(
                        resp.replace("```json", "").replace("```", "").strip()
                    )
            except Exception as e:
                self.log(f"Founder Extraction Failed: {e}")

        if not founders:
            self.log("No founders identified. Skipping targeted search.")
            return

        self.log(f"Investigating Verified Founders: {[f['name'] for f in founders]}")

        # 2. Targeted Search per Founder (Enhanced & Anchored)
        for f in founders[:3]:  # Limit to top 3 to save time/cost
            name = f["name"]

            # Direct LinkedIn URL Sniffing using Dorking
            q_li = f'"{name}" "{self.company}" site:linkedin.com/in'
            li_res = self.search_tavily(q_li, 1)
            if not li_res:
                li_res = self.search_brave(q_li, 1)
            for r in li_res:
                r["content"] = (
                    f"[FOUNDER LINKEDIN: {name}] {r.get('url')} - " + r["content"]
                )
            self.sources.extend(li_res)

            # Background Search
            q1 = f'"{name}" "{self.company}" previous startups exits failures history university research publications background'
            res1 = self.search_tavily(q1, 2)
            for r in res1:
                r["content"] = f"[FOUNDER TRACK RECORD: {name}] " + r["content"]
            self.sources.extend(res1)

            self.log(f"Deep dived into {name}.")

        # 3C. Standard Deep Dive (Tech + Market)
        tech_queries = [
            f"{self.company} architecture API documentation github",
            f"{self.company} tech stack llm infrastructure",
            f"{self.company} security compliance SOC2 ISO27001",
        ]
        for q in tech_queries:
            self.sources.extend(self.search_exa(q, 2))

        market_queries = [
            f"{self.company} pricing plans comparison",
            f"{self.company} market size TAM SAM SOM",
            f"{self.company} competitors pricing crunchbase g2",
        ]
        for q in market_queries:
            self.sources.extend(self.search_tavily(q, 2) or self.search_ddg(q, 2))

        self.log(f"Total Sources: {len(self.sources)}")

    def _iron_firewall(self):
        """Pre-Phase 3.5: The Multi-Factor Authentication Firewall (Confidence Scoring)."""
        self.log("Phase 3.5a: Engaging The Iron Firewall (Dynamic Confidence Purge)...")
        clean_sources = []
        target_name_lower = self.company.lower()

        # Determine if we are in Stealth Mode (No official team and no strong keywords found)
        official_team = getattr(self, "official_team", [])
        stealth_mode = len(official_team) == 0 and len(self.truth_keywords) == 0
        if stealth_mode:
            self.log("Target in stealth mode - using relaxed filtering")
            self.stealth_mode = True
        else:
            self.stealth_mode = False

        for s in self.sources:
            # 1. Exempt Official/Safe Sources
            if s.get("source") in [
                "Scrapling (Home Page)",
                "Scrapling (Subpage)",
                "Upload",
                "LinkedIn (Apify)",
                "OSINT X-Ray",
                "Apify",
            ]:
                clean_sources.append(s)
                continue

            text_blob = (
                str(s.get("title", "")) + " " + str(s.get("content", ""))
            ).lower()

            # 2. Chinese SEO Spam Filter (Burn on sight)
            spam_words = ["截图", "知乎", "快捷键", "下载", "教程", "怎么用"]
            if any(w in text_blob for w in spam_words):
                self.log(f"Firewall Blocked (SEO Spam): {s.get('title')}")
                continue

            # 3. Fiction/Game Noise Filter (Burn on sight)
            fiction_words = [
                "novel",
                "chapter",
                "anime",
                "manga",
                "episode",
                "tbate",
                "wrestling",
                "monopoly",
            ]
            if any(w in text_blob for w in fiction_words):
                self.log(f"Firewall Blocked (Fiction/Game): {s.get('title')}")
                continue

            # 4. Strict Name Boundary Match (Gatekeeper)
            # It must contain the exact word bounded by non-alphanumeric chars to prevent Sevalla passing for Sevren
            # Relax slightly for URLs
            name_pattern = r"\b" + re.escape(target_name_lower) + r"\b"
            url_match = target_name_lower in s.get("url", "").lower()
            if not url_match and not re.search(name_pattern, text_blob):
                self.log(f"Firewall Blocked (Exact Name Missing): {s.get('title')}")
                continue

            # 5. Multi-Factor Confidence Scoring (Only if not in stealth mode)
            if not stealth_mode:
                confidence_score = 0

                # A. URL/Domain Match
                domain_core = self.domain.replace("www.", "").split(".")[0]
                if domain_core in s.get("url", "").lower():
                    confidence_score += 2

                # B. Team Match
                for team_member in official_team:
                    if team_member.get("name", "").lower() in text_blob:
                        confidence_score += 2
                        break

                # C. Truth Keyword Match
                for kw in self.truth_keywords:
                    if kw in text_blob:
                        confidence_score += 1
                        break

                # Verdict
                if confidence_score >= 1:
                    clean_sources.append(s)
                else:
                    self.log(
                        f"Firewall Blocked (Low Confidence Score 0): {s.get('title')} - Contains name but lacks supporting features."
                    )
            else:
                # In Stealth mode, exact name match is enough
                clean_sources.append(s)

        self.log(
            f"Iron Firewall complete. Kept {len(clean_sources)} out of {len(self.sources)} sources."
        )
        self.sources = clean_sources

    def phase_audit_consistency(self):
        """Phase 3.5: Audit sources for identity mismatch (e.g. wrong company with same name)"""
        self._iron_firewall()  # Run hard physical filter FIRST

        self.log("Phase 3.5b: LLM Auditing Sources for Consistency...")

        # Prepare context for LLM Audit
        # We limit to title/url/snippet to save context window
        source_list = []
        for i, s in enumerate(self.sources):
            source_list.append(
                f"ID {i}: Title='{s.get('title')}' URL='{s.get('url')}' Snippet='{s.get('content', '')[:200]}'"
            )

        audit_prompt = f"""
        You are a QA Lead Auditor.
        Target Company: {self.company}
        Target URL: {self.url}

        Task: Review the list of gathered sources. Identify any source that is IRRELEVANT.
        CRITICAL: You MUST aggressively flag sources that refer to fiction novels, video games, fictional characters (e.g., magic schools, anime), or completely unrelated companies with the same name.

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
                self.log(
                    f"AUDIT ALERT: Excluding {len(exclude_ids)} bad sources. Reason: {audit_result.get('reason')}"
                )
                # Filter sources
                self.sources = [
                    s for i, s in enumerate(self.sources) if i not in exclude_ids
                ]
            else:
                self.log("Audit Passed: No identity conflicts detected.")

        except Exception as e:
            self.log(f"Audit Warning: Failed to run consistency check. {e}")

    def phase_4_synthesis(self):
        self.log("Phase 4: Synthesis using KERNEL Pattern...")

        # Deduplicate sources by URL
        seen_urls = set()
        unique_sources = []
        for s in self.sources:
            if s.get("url") and s["url"] not in seen_urls:
                unique_sources.append(s)
                seen_urls.add(s["url"])

        # --- RERANKING INTEGRATION (OPE-4) ---
        # Apply two-stage reranking to improve source relevance
        if len(unique_sources) > 10:
            self.log(f"Applying two-stage reranking to {len(unique_sources)} sources...")
            try:
                # Convert sources to SearchResult format for reranking
                rerank_candidates = []
                for i, s in enumerate(unique_sources):
                    rerank_candidates.append({
                        'doc_id': str(i),
                        'title': s.get("title", ""),
                        'content': s.get("content", ""),
                        'score': 0.5  # Default score
                    })
                
                # Simple reranking based on title/content relevance to company name
                query = f"{self.company} investment research startup funding"
                query_tokens = set(re.findall(r'\b[a-zA-Z]+\b', query.lower()))
                
                scored_sources = []
                for candidate in rerank_candidates:
                    title_tokens = set(re.findall(r'\b[a-zA-Z]+\b', candidate['title'].lower()))
                    content_tokens = set(re.findall(r'\b[a-zA-Z]+\b', candidate['content'].lower()))
                    
                    # Calculate relevance score
                    title_overlap = len(query_tokens & title_tokens) / max(len(query_tokens), 1)
                    content_overlap = len(query_tokens & content_tokens) / max(len(query_tokens), 1)
                    exact_match = 1.0 if self.company.lower() in candidate['title'].lower() else 0.0
                    
                    score = (title_overlap * 0.4 + content_overlap * 0.3 + exact_match * 0.3)
                    scored_sources.append((score, int(candidate['doc_id'])))
                
                # Sort by score descending
                scored_sources.sort(key=lambda x: x[0], reverse=True)
                
                # Reorder unique_sources
                reranked = []
                for score, idx in scored_sources:
                    reranked.append(unique_sources[idx])
                
                unique_sources = reranked
                self.log(f"Reranking complete. Top source: {unique_sources[0].get('title', 'N/A')[:50]}...")
            except Exception as e:
                self.log(f"Reranking warning: {e}. Continuing with original order.")
        # --- END RERANKING INTEGRATION ---

        # Create Citation Map (Markdown Links)
        citations = []
        context_blob = ""
        for i, s in enumerate(unique_sources):
            ref_num = i + 1
            raw_title = s.get("title") or "Unknown Source"
            title = str(raw_title).replace("[", "(").replace("]", ")")
            url = s.get("url", "#")
            citations.append(f"[{ref_num}] [{title}]({url})")

            content = s.get("content") or ""
            context_blob += f"Source [{ref_num}]: {str(content)[:2000]}\n\n"

        self.usage["llm_input_chars"] += len(context_blob)

        # --- AGENT 1: The Purifier (Extract Facts into JSON) ---
        self.log("Agent 1 (Purifier): Extracting core facts...")
        prompt_agent1 = f"""
        Task: Extract factual data strictly about {self.company} (Domain: {self.domain}) into a structured JSON format.
        Input:
        {context_blob}

        CRITICAL ENTITY FILTERING (ANTI-HALLUCINATION):
        1. YOU MUST IGNORE any sources or paragraphs that are clearly about a different company with a similar name. 
        2. For example, if {self.company} is "Wavemotion AI" (domain: wavemotionai.com), and a source talks about "WaveForms AI" raising $40M, YOU MUST IGNORE IT. Do not attribute data from similarly named companies to {self.company}.
        3. If you only find data about wrong companies, leave the JSON fields empty. DO NOT HALLUCINATE.
        
        Constraints:
        - Output ONLY valid JSON. No markdown wrappers.
        - Ignore data about fictional characters (e.g., novels, games).
        - If a section lacks data for the specific target company, return an empty string or empty list.

        Output Format:
        {{
            "executive_summary": "Company overview and mission",
            "swot": {{"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}},
            "product_features": [],
            "competitors": [{{"name": "", "features": "", "pricing": ""}}],
            "social_sentiment": "Summary of real user sentiment",
            "business_model": "Revenue and pricing strategy",
            "traction_and_risks": "Funding, traffic, and legal risks",
            "founding_team": [{{"name": "", "background": ""}}],
            "data_consistency": "Conflicts between PR and reality based on [TRAFFIC DATA] or [HIRING SIGNAL]",
            "exit_strategy": "Potential acquirers or IPO landscape"
        }}
        """

        try:
            resp1 = gateway.generate(prompt_agent1, "Return valid JSON only.")
            facts_json = resp1.replace("```json", "").replace("```", "").strip()
            # Test parse
            json.loads(facts_json)
        except Exception as e:
            self.log(f"Agent 1 Failed: {e}. Falling back to monolithic generation.")
            facts_json = context_blob  # Fallback to raw text if JSON fails

        # --- AGENT 2: The Interrogator (Generate 5 Kill Questions) ---
        self.log("Agent 2 (Interrogator): Generating Due Diligence questions...")
        prompt_agent2 = f"""
        Task: Generate 5 aggressive, highly specific due diligence questions to ask the founders of {self.company}.
        Input:
        {facts_json}

        Constraints:
        - Output ONLY a JSON list of 5 strings. No markdown wrappers.
        - Base questions strictly on the weaknesses, funding gaps, or missing data in the Input.
        - Do not ask generic questions ("What is your vision?").

        Output Format:
        [
            "Question 1...",
            "Question 2...",
            "Question 3...",
            "Question 4...",
            "Question 5..."
        ]
        """

        try:
            resp2 = gateway.generate(prompt_agent2, "Return valid JSON list only.")
            questions_json = resp2.replace("```json", "").replace("```", "").strip()
            questions = json.loads(questions_json)
        except Exception as e:
            self.log(f"Agent 2 Failed: {e}")
            questions = [
                "What is the specific proprietary advantage of your technology?",
                "Can you provide detailed financial metrics and customer acquisition costs?",
                "What is your strategy for overcoming regulatory hurdles?",
            ]

        # --- AGENT 3: The Formatter (Build the final Markdown) ---
        self.log("Agent 3 (Formatter): Assembling the final report...")
        # Add questions into the facts payload for the formatter
        formatting_payload = f"FACTS:\n{facts_json}\n\nINTERROGATION QUESTIONS:\n{json.dumps(questions)}"

        prompt_agent3 = f"""
        Task: Write a comprehensive, highly analytical Investment Memo for {self.company}. Ensure the final report provides deep strategic value.

        Input:
        {formatting_payload}

        CRITICAL VC ANALYSIS CONSTRAINTS (ANTI-FLUFF):
        1. NO HALLUCINATIONS: Do NOT invent raw facts, names, numbers, or fictional competitors. 
        2. HONEST SCARCITY: If specific factual data (e.g., funding, traction, pricing) is missing from the Input, you MUST explicitly state "Data Undisclosed" or "Not publicly available". Do NOT try to hide the lack of data with generic industry boilerplate.
        3. DEDUCTIVE DEPTH (How to expand without fluff): While you cannot invent facts, you MUST provide deep strategic commentary on the implications of the information you *do* have. For example:
           - If they are a stealth startup, analyze what challenges a stealth startup in this specific niche will inevitably face.
           - If their tech stack is known but revenue isn't, analyze the commercial viability and typical go-to-market motion for that tech stack.
        4. Do NOT write a References section at the end.
        5. Do NOT number the headers.
        6. For the "Founding Team & Track Record" section, you MUST include any LinkedIn URLs found in the Input facts. If the team is hidden, state "Founding Team Undisclosed".

        Output Format:
        Must include EXACTLY these sections with these headers in this EXACT order:
        # {self.company} Pre-Screen Memo

        ## Executive Summary
        (Provide a sharp, 2-3 paragraph summary. Include a Markdown table for SWOT Analysis: | Strengths | Weaknesses | Opportunities | Threats |)

        ## The Problem
        ### Current/Traditional Solutions
        (Analyze the macro industry status quo. What existing solutions or traditional approaches does {self.company} aim to replace?)

        ### Pain Points
        (Analyze 2-4 specific pain points in this market. If {self.company} has not published their exact metrics, analyze the *typical* quantifiable impacts in this sector. Explain why existing solutions fail.)

        ## Company Overview & Solution
        ### What They Do
        (Clear description of the company's product/service)

        ### How They Solve The Pain Points
        (Create a mapping table: | Pain Point | Their Solution | Impact |)

        ## Product Deep Dive
        ## Market Landscape
        (Markdown table: | Competitor | Features | Pricing |)
        ## Social Sentiment & Risk
        ## Business Model
        ## Traction & Risks
        ## Founding Team & Track Record
        ## Data Consistency Check & Hidden Signals
        ## Exit Strategy & M&A Landscape

        ## Due Diligence Interrogation
        (List the 5 questions provided in the Input. This must be the very last section before the references.)
        """

        report = gateway.generate(prompt_agent3, "Output ONLY the Markdown report.")

        # ---- PHASE 4.5: TRANSLATION (If requested) ----
        if report and self.language.lower() != "english":
            self.log(
                f"Phase 4.5: Translating high-density English report to {self.language}..."
            )
            translation_prompt = f"""
            You are a professional financial translator and investment analyst.
            Your task is to translate the following deep research report into {self.language}.

            CRITICAL RULES:
            1. DO NOT summarize or omit ANY data, numbers, or company names. Keep the exact factual density of the original.
            2. Maintain all Markdown formatting perfectly, especially tables, headers, and citation brackets like [1].
            3. Translate table headers properly.
            4. If a term is a specific product name or proper noun (like 'Cloudflare', 'Series A'), keep the English term or use industry-standard terminology.
            5. Ensure the tone is objective, professional, and native to an investment memo.

            Original Report:
            {report}
            """
            translated_report = gateway.generate(
                translation_prompt,
                f"Output ONLY the perfectly translated markdown report in {self.language}.",
            )

            if translated_report:
                report = translated_report
                self.usage["llm_input_chars"] += (
                    len(report) * 2
                )  # Rough estimate of translation token usage
                self.usage["llm_output_chars"] += len(translated_report)

        # Update usage counter for output tokens (Approx)
        if report:
            self.usage["llm_output_chars"] += len(report)

        if not report:
            self.log("Error: LLM returned None for report generation.")
            return (
                "# Analysis Failed\n\nDeep Research collected relevant sources, but the LLM failed to synthesize the final report due to a timeout or safety filter.\n\n## Data gathered\n"
                + f"{len(unique_sources)} sources found."
            )

        # FORCE APPEND REFERENCES (Programmatic, Clickable)
        # We strip any LLM-hallucinated references first to avoid duplicates
        if "## References" in report:
            report = report.split("## References")[0].strip()

        # Strip any trailing markdown code block backticks that might cause the references to be rendered inside a code block
        report = report.strip()
        while report.endswith("```"):
            report = report[:-3].strip()
        if report.endswith("```markdown"):
            report = report[:-11].strip()

        report += "\n\n## References\n"
        for c in citations:
            report += f"- {c}\n"

        return report

    def run(self):
        self.phase_1_broad_scan()
        self.phase_1_5_rerank_sources()  # NEW: Rerank sources for better quality
        self.phase_2_gap_analysis()
        self.phase_3_deep_dive()
        self.phase_audit_consistency()  # New Audit Step
        return self.phase_4_synthesis()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        engine = ResearchEngine(sys.argv[1])
        report = engine.run()
        print(report)
    else:
        print("Usage: python research_engine.py <url>")
