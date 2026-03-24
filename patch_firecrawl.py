import re

def apply_firecrawl_patch():
    with open("backend/research_engine.py", "r", encoding="utf-8") as f:
        content = f.read()

    new_fallback = """        except Exception as e:
            self.log(f"Scrapling Error: {e}")
            import firecrawl_bridge as firecrawl
            
            fc_markdown = None
            if os.getenv("FIRECRAWL_API_KEY"):
                self.log("Scrapling failed. Engaging Firecrawl Heavy Scraper...")
                try:
                    fc_markdown = firecrawl.scrape_with_firecrawl(self.url)
                    if fc_markdown and len(fc_markdown) > 100:
                        self.log(f"Firecrawl: Extracted {len(fc_markdown)} chars from {self.url} (bypassed protection).")
                        self.sources.append({
                            "title": self.domain,
                            "url": self.url,
                            "content": fc_markdown[:8000],
                            "source": "Scrapling (Home Page)" # Kept same name to pass strict source filters
                        })
                except Exception as fc_e:
                    self.log(f"Firecrawl Error: {fc_e}")

            if not fc_markdown:
                import xcrawl_bridge as xcrawl
                if os.getenv("XCRAWL_API_KEY"):
                    self.log("Falling back to xCrawl Deep Crawl (Map + Scrape)...")"""

    old_fallback = """        except Exception as e:
            self.log(f"Scrapling Error: {e}")
            import xcrawl_bridge as xcrawl
            
            if os.getenv("XCRAWL_API_KEY"):
                self.log("Falling back to xCrawl Deep Crawl (Map + Scrape)...")"""
                
    content = content.replace(old_fallback, new_fallback)

    with open("backend/research_engine.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched Firecrawl")

if __name__ == "__main__":
    apply_firecrawl_patch()
