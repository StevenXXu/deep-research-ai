import json
import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()


DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

DEFAULT_USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
)


def _parse_dict(raw_value: Optional[str]) -> Optional[Dict[str, str]]:
    if not raw_value:
        return None
    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, dict):
            # Ensure string keys/values
            return {str(k): str(v) for k, v in parsed.items()}
    except json.JSONDecodeError:
        pass
    return None


def _parse_float(raw_value: Optional[str]) -> Optional[float]:
    if not raw_value:
        return None
    try:
        return float(raw_value)
    except (ValueError, TypeError):
        return None


@dataclass
class ScraperConfig:
    headers: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_HEADERS))
    cookies: Dict[str, str] = field(default_factory=dict)
    proxy_url: Optional[str] = None
    scroll_wait: float = 1.5
    wait_for_selector: Optional[str] = None
    wait_for: str = "networkidle"
    max_scrolls: int = 0
    user_agent: str = DEFAULT_USER_AGENT

    @classmethod
    def from_env(cls) -> "ScraperConfig":
        config = cls()
        headers = _parse_dict(os.getenv("SCRAPER_HEADERS"))
        cookies = _parse_dict(os.getenv("SCRAPER_COOKIES"))
        proxy_url = os.getenv("SCRAPER_PROXY_URL")
        scroll_wait = _parse_float(os.getenv("SCRAPER_SCROLL_WAIT"))
        wait_for_selector = os.getenv("SCRAPER_WAIT_FOR_SELECTOR")
        wait_for = os.getenv("SCRAPER_WAIT_FOR", config.wait_for)
        raw_max_scrolls = os.getenv("SCRAPER_MAX_SCROLLS")
        try:
            max_scrolls = int(raw_max_scrolls) if raw_max_scrolls is not None else config.max_scrolls
        except ValueError:
            max_scrolls = config.max_scrolls
        user_agent = os.getenv("SCRAPER_USER_AGENT", config.user_agent)

        if headers:
            config.headers = headers
        if cookies:
            config.cookies = cookies
        if proxy_url:
            config.proxy_url = proxy_url
        if scroll_wait is not None:
            config.scroll_wait = scroll_wait
        if wait_for_selector:
            config.wait_for_selector = wait_for_selector
        config.wait_for = wait_for
        config.max_scrolls = max_scrolls
        config.user_agent = user_agent
        return config

    def _headers_with_user_agent(self) -> Dict[str, str]:
        headers = dict(self.headers or {})
        if self.user_agent:
            headers.setdefault("User-Agent", self.user_agent)
        return headers

    def to_stealthy_fetcher_kwargs(self) -> Dict[str, Any]:
        
        # Scrapling/Playwright expects cookies as an array of dicts or None, not a single dict
        # So we convert {"key": "value"} to a format acceptable by playwright if needed, 
        # or just pass None if empty
        formatted_cookies = None
        
        if self.cookies:
            formatted_cookies = []
            for k, v in self.cookies.items():
                # Note: Playwright usually requires 'domain' or 'url' to be set, 
                # but we might not have it here. Passing an empty list or None is safer 
                # if we don't have properly formatted cookies.
                pass
            # For now, just bypass dict cookies to prevent "Expected array | null, got object" error
            formatted_cookies = None

        kwargs: Dict[str, Any] = {
            "headers": self._headers_with_user_agent(),
            "cookies": formatted_cookies,
            "wait_for": self.wait_for,
        }
        if False: # DISABLED: self.proxy_url:
            # Playwright requires proxy as a dict if it has auth
            # Parse http://user:pass@host:port
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.proxy_url)
                if parsed.username and parsed.password:
                    kwargs["proxy"] = {
                        "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
                        "username": parsed.username,
                        "password": parsed.password
                    }
                else:
                    kwargs["proxy"] = {"server": self.proxy_url}
            except Exception:
                kwargs["proxy"] = {"server": self.proxy_url}
                
        if self.scroll_wait:
            kwargs["scroll_wait"] = self.scroll_wait
        if self.wait_for_selector:
            kwargs["wait_for_selector"] = self.wait_for_selector
        if self.max_scrolls:
            kwargs["max_scrolls"] = self.max_scrolls
        return kwargs

    def to_apify_run_input(self, base_input: Dict[str, Any]) -> Dict[str, Any]:
        run_input = base_input.copy()
        run_input["customUserAgent"] = self.user_agent
        run_input["headers"] = self._headers_with_user_agent()
        if self.cookies:
            run_input["cookies"] = self.cookies
        if False: # DISABLED: self.proxy_url:
            run_input["proxyConfiguration"] = {
                "useApifyProxy": False,
                "proxyUrls": [self.proxy_url],
            }
        if self.wait_for_selector:
            run_input["waitForSelector"] = self.wait_for_selector
        if self.wait_for:
            run_input["waitUntil"] = self.wait_for
        if self.scroll_wait:
            run_input["windowScrollDelayMs"] = int(self.scroll_wait * 1000)
        if self.max_scrolls:
            run_input["scrollerMaxDepth"] = self.max_scrolls
        return run_input


DEFAULT_CONFIG = ScraperConfig()
