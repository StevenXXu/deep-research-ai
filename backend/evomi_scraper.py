"""
Evomi Scraper API Integration
Handles async scraping with automatic Cloudflare/WAF bypass
"""

import os
import time
import requests
from typing import Optional, Dict, Any

# Evomi API Configuration
EVOMI_API_KEY = os.getenv("EVOMI_API_KEY", "")
EVOMI_BASE_URL = "https://scrape.evomi.com/api/v1/scraper"

def scrape_url(
    url: str,
    timeout: int = 180,  # Increased to 3 minutes
    poll_interval: int = 5,
    max_polls: int = 36,  # 180s / 5s = 36 polls max
    render_js: bool = True,
    country: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scrape a URL using Evomi's Scraper API with async polling.
    
    Args:
        url: Target URL to scrape
        timeout: Total timeout in seconds
        poll_interval: Seconds between status checks
        max_polls: Maximum number of polling attempts
        render_js: Whether to render JavaScript (uses browser mode)
        country: Country code for geotargeting (e.g., "US", "AU")
    
    Returns:
        Dict with 'success', 'content', 'error' keys
    """
    if not EVOMI_API_KEY:
        return {
            "success": False,
            "content": None,
            "error": "EVOMI_API_KEY not configured"
        }
    
    headers = {
        "x-api-key": EVOMI_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Submit scraping task - use GET request with query params
        print(f"[EVOMI] Submitting task for {url}...", flush=True)
        
        # Build query parameters
        params = {
            "url": url,
            "mode": "browser",  # Use browser mode for JS rendering
            "proxy_type": "premium",  # Residential proxies for better success
            "render": "true" if render_js else "false"
        }
        if country:
            params["proxy_country"] = country
        
        response = requests.get(
            f"{EVOMI_BASE_URL}/realtime",
            params=params,
            headers=headers,
            timeout=90  # Increased timeout for slow responses
        )
        
        print(f"[EVOMI] Response: status={response.status_code}", flush=True)
        
        if response.status_code == 200:
            # Immediate success (simple sites)
            data = response.json()
            content = data.get("content") or data.get("html") or data.get("body")
            if content:
                print(f"[EVOMI] Got immediate response", flush=True)
                return {
                    "success": True,
                    "content": content,
                    "error": None
                }
            # Fall through to polling if no content
        
        if response.status_code == 202:
            # Async task - need to poll
            data = response.json()
            task_id = data.get("task_id")
            check_url = data.get("check_url")
            
            if not check_url:
                return {
                    "success": False,
                    "content": None,
                    "error": f"No check_url in response: {data}"
                }
            
            print(f"[EVOMI] Task queued: {task_id}. Polling...", flush=True)
            
            # Poll for results with smart error detection
            consecutive_errors = 0
            for i in range(max_polls):
                time.sleep(poll_interval)
                
                poll_response = requests.get(
                    f"https://scrape.evomi.com{check_url}",
                    headers=headers,
                    timeout=30
                )
                
                if poll_response.status_code == 200:
                    result = poll_response.json()
                    consecutive_errors = 0  # Reset error counter
                    
                    # Check if task is complete
                    if result.get("status") == "completed":
                        content = result.get("content") or result.get("html") or result.get("body")
                        if content:
                            print(f"[EVOMI] Task completed after {i+1} polls", flush=True)
                            return {
                                "success": True,
                                "content": content,
                                "error": None
                            }
                        else:
                            return {
                                "success": False,
                                "content": None,
                                "error": f"Task completed but no content: {result.keys()}"
                            }
                    
                    elif result.get("status") == "failed":
                        return {
                            "success": False,
                            "content": None,
                            "error": f"Task failed: {result.get('error', 'Unknown error')}"
                        }
                    
                    # Still processing
                    print(f"[EVOMI] Poll {i+1}: {result.get('status', 'unknown')}", flush=True)
                
                elif poll_response.status_code == 500:
                    # Server error - track consecutive 500s
                    consecutive_errors += 1
                    print(f"[EVOMI] Poll {i+1}: HTTP 500 (server error, consecutive={consecutive_errors})", flush=True)
                    if consecutive_errors >= 3:
                        print(f"[EVOMI] Server error detected 3 times. Abandoning task.", flush=True)
                        return {
                            "success": False,
                            "content": None,
                            "error": f"Evomi server error (HTTP 500) - abandoning after {consecutive_errors} consecutive errors"
                        }
                else:
                    consecutive_errors = 0  # Reset on non-500 response
                    print(f"[EVOMI] Poll {i+1}: HTTP {poll_response.status_code}", flush=True)
            
            # Timeout reached
            return {
                "success": False,
                "content": None,
                "error": f"Timeout after {max_polls * poll_interval}s"
            }
        
        # Unexpected status code
        return {
            "success": False,
            "content": None,
            "error": f"Unexpected status {response.status_code}: {response.text[:200]}"
        }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "content": None,
            "error": "Request timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "content": None,
            "error": str(e)
        }


def check_credits() -> Dict[str, Any]:
    """Check remaining credits for the Evomi account."""
    if not EVOMI_API_KEY:
        return {"error": "EVOMI_API_KEY not configured"}
    
    headers = {
        "x-api-key": EVOMI_API_KEY
    }
    
    try:
        response = requests.get(
            "https://scrape.evomi.com/api/v1/credits",
            headers=headers,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}
