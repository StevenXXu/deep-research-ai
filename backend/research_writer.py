import os
import sys
import json
import time
from datetime import datetime
import subprocess

# Add Root to Path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from llm_gateway import gateway
import discord_connector as dc

# Deep Research Writer
# 1. Navigates to a URL
# 2. Takes a full-page screenshot
# 3. Scrapes text
# 4. Generates an "Investment Grade" Analysis

OUTPUT_DIR = "workspace/research_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_research(url, target_email=None):
    print(f"[RESEARCH] Analyzing: {url}")
    dc.post("cipher", "START", f"Starting Deep Research on {url}")
    
    timestamp = int(time.time())
    site_name = url.split("//")[-1].replace("/", "_")
    screenshot_path = os.path.abspath(f"{OUTPUT_DIR}/{site_name}_{timestamp}.png")
    
    # 1. Browser Automation (Node.js wrapper for Playwright)
    # We will create a small temporary JS script to do the heavy lifting
    js_script = f"""
    const {{ chromium }} = require('playwright');
    const fs = require('fs');

    (async () => {{
      const browser = await chromium.launch();
      const page = await browser.newPage();
      try {{
        console.log("Navigating...");
        await page.goto('{url}', {{ waitUntil: 'networkidle' }});
        
        console.log("Screenshotting...");
        await page.screenshot({{ path: '{screenshot_path.replace(os.sep, "/")}', fullPage: true }});
        
        const content = await page.innerText('body');
        console.log("__CONTENT_START__");
        console.log(content);
        console.log("__CONTENT_END__");
      }} catch (e) {{
        console.error(e);
      }} finally {{
        await browser.close();
      }}
    }})();
    """
    
    js_path = f"{OUTPUT_DIR}/temp_scraper_{timestamp}.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_script)
        
    # Execute Node
    try:
        print("[RESEARCH] Browsing site...")
        result = subprocess.run(["node", js_path], capture_output=True, text=True, encoding="utf-8")
        
        # Extract Content
        output = result.stdout
        if "__CONTENT_START__" in output:
            raw_text = output.split("__CONTENT_START__")[1].split("__CONTENT_END__")[0]
        else:
            raw_text = "No content extracted."
            print(f"[ERROR] Browser Output: {output}")
            
        print(f"[RESEARCH] Extracted {len(raw_text)} chars.")
        dc.post("cipher", "PROGRESS", f"Scraped site. Screenshot saved.")

        # 2. AI Analysis (Weaver/Analyst Role)
        prompt = f"""
        You are an Investment Analyst and Tech Writer.
        
        Target URL: {url}
        Raw Content Scraped from Landing Page:
        {raw_text[:8000]} (Truncated)
        
        Task: Write a "Deep Dive" analysis of this product.
        
        Structure:
        1. **The Hook:** What is this? Why is it interesting?
        2. **Value Prop:** What problem does it solve?
        3. **Mechanism:** How does it work? (Infer from text)
        4. **Bull Case:** Why could this be huge?
        5. **Bear Case:** What are the risks?
        
        Tone: Professional, Insightful, "VC Twitter" style.
        Format: Markdown.
        """
        
        analysis = gateway.generate(prompt, "You are a top-tier tech analyst.")
        
        # 3. Save Report
        report_path = f"{OUTPUT_DIR}/{site_name}_{timestamp}_Analysis.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Deep Dive: {url}\n\n")
            f.write(f"![Screenshot]({os.path.basename(screenshot_path)})\n\n")
            f.write(analysis)
            
        print(f"[SUCCESS] Report saved: {report_path}")
        dc.post("cipher", "DONE", f"Research Complete. Report: `{report_path}`")
        
        # Email Logic
        if target_email:
            print(f"[EMAIL] Sending report to {target_email}...")
            # Use the existing smtp-send logic (calling via subprocess)
            email_cmd = [
                "python", "skills/smtp-send/scripts/send_email.py",
                "--to", target_email,
                "--subject", f"Deep Research: {site_name}",
                "--body", f"Your research report for {url} is attached.",
                "--attachment", report_path,
                "--attachment", screenshot_path # Send both MD and PNG
            ]
            subprocess.run(email_cmd)
            print(f"[EMAIL] Sent.")
        
        # Cleanup
        os.remove(js_path)
        
        return report_path

    except Exception as e:
        print(f"[ERROR] Research failed: {e}")
        dc.post("cipher", "ERROR", f"Research failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        email = None
        if len(sys.argv) > 2:
            email = sys.argv[2]
        run_research(target_url, email)
    else:
        print("Usage: python research_writer.py <url> [email]")
