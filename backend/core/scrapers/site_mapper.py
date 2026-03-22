import urllib.parse
import re
import json

class SiteMapper:
    """
    SiteMapper Engine (BFS Topology Mapper)
    Analyzes all extracted hrefs from a homepage to detect the site structure,
    score the internal links, and identify 'Golden URLs' for deep crawling.
    Also detects single-page/vaporware apps.
    """

    def __init__(self, base_url):
        self.base_url = base_url
        if not self.base_url.startswith("http"):
            self.base_url = "https://" + self.base_url
        
        self.parsed_base = urllib.parse.urlparse(self.base_url)
        self.base_netloc = self.parsed_base.netloc.replace("www.", "")

        # P0: Team & Background
        self.p0_keywords = ['/about', '/team', '/company', '/investors', 'about-us', 'about_us']
        
        # P1: Business Model
        self.p1_keywords = ['/pricing', '/plans', '/enterprise', 'pricing']
        
        # P2: Product Core
        self.p2_keywords = ['/product', '/features', '/technology', '/how-it-works', 'products']
        
        # P3: Market Validation
        self.p3_keywords = ['/customers', '/case-studies', '/success-stories', 'cases']

        # Blacklist (Functional or Legal noise)
        self.blacklist = [
            '/login', '/signup', '/cart', '/privacy', '/terms', '/legal', 
            'login', 'register', 'signin', 'auth', 'password'
        ]

    def _normalize_and_check_origin(self, href):
        if not href or href.startswith('javascript:') or href.startswith('mailto:') or href.startswith('tel:'):
            return None
            
        # Strip anchor links and queries for clean deduplication
        href = href.split('#')[0].split('?')[0]
        if not href:
            return None

        # Resolve relative URLs
        full_url = urllib.parse.urljoin(self.base_url, href)
        
        # Check Origin
        parsed_target = urllib.parse.urlparse(full_url)
        target_netloc = parsed_target.netloc.replace("www.", "")
        
        if target_netloc != self.base_netloc and not target_netloc.endswith("." + self.base_netloc):
            return None # Drop external links

        return full_url

    def _score_url(self, url):
        url_lower = url.lower()
        
        # Check blacklist
        if any(b in url_lower for b in self.blacklist):
            return -1, "Blacklisted"

        # Check Priorities (Highest P0 -> P3)
        if any(k in url_lower for k in self.p0_keywords):
            return 100, "Team & Background"
            
        if any(k in url_lower for k in self.p1_keywords):
            return 80, "Business Model"
            
        if any(k in url_lower for k in self.p2_keywords):
            return 60, "Product Core"
            
        if any(k in url_lower for k in self.p3_keywords):
            return 40, "Market Validation"
            
        return 0, "Other"

    def map_site(self, extracted_hrefs):
        """
        Takes a list of raw hrefs extracted from the target's homepage DOM.
        Returns a structured JSON dict with the site topology analysis.
        """
        unique_valid_urls = set()
        
        for href in extracted_hrefs:
            norm_url = self._normalize_and_check_origin(href)
            # Ensure we don't count the homepage itself as an internal sub-page
            if norm_url and norm_url.rstrip('/') != self.base_url.rstrip('/'):
                unique_valid_urls.add(norm_url)

        scored_urls = []
        for url in unique_valid_urls:
            score, category = self._score_url(url)
            if score > 0:
                scored_urls.append({"url": url, "score": score, "category": category})

        # Sort by highest score, then alphabetically to be deterministic
        scored_urls.sort(key=lambda x: (x["score"], x["url"]), reverse=True)

        # Pick top 5 golden URLs (or however many we want to deep dive)
        golden_urls = [{"url": item["url"], "category": item["category"]} for item in scored_urls[:5]]

        total_links = len(unique_valid_urls)
        # Empty shell detector: 1 or 0 actual internal sub-pages (excluding `#` anchors)
        is_single_page = total_links <= 1

        return {
            "domain": self.base_netloc,
            "total_internal_links_found": total_links,
            "is_single_page_site": is_single_page,
            "golden_urls_selected": golden_urls
        }

if __name__ == "__main__":
    # Quick Test Execution
    mapper = SiteMapper("https://linear.app/")
    mock_hrefs = [
        "/",
        "#features",
        "/about",
        "https://linear.app/pricing",
        "/features",
        "https://twitter.com/linear",
        "/login",
        "/privacy",
        "/customers",
        "/unknown-page"
    ]
    result = mapper.map_site(mock_hrefs)
    print(json.dumps(result, indent=2))