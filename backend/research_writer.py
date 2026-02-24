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
from exa_py import Exa

# Deep Research Writer
# 1. Navigates to a URL (Playwright)
# 2. Searches for Context (Exa)
# 3. Generates "Investment Grade" Analysis

OUTPUT_DIR = "workspace/research_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load Exa Key from Root Env
# The root_dir logic handles loading .env.google, but we need .env too
load_dotenv(os.path.join(root_dir, ".env"))
EXA_KEY = os.getenv("EXA_API_KEY")

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

        # 2. Exa Search (Context Augmentation)
        exa_context = "No external context found."
        if EXA_KEY:
            try:
                print("[RESEARCH] Querying Exa for context...")
                exa = Exa(EXA_KEY)
                # Extract domain name for query
                domain = url.split("//")[-1].split("/")[0]
                
                # Search for News & Competitors
                search_response = exa.search_and_contents(
                    f"{domain} startup funding competitors news",
                    type="neural",
                    use_autoprompt=True,
                    num_results=3,
                    text=True
                )
                
                exa_results = []
                for res in search_response.results:
                    exa_results.append(f"Source: {res.title} ({res.url})\nSummary: {res.text[:500]}...")
                
                exa_context = "\n\n".join(exa_results)
                print(f"[RESEARCH] Found {len(exa_results)} external sources.")
                dc.post("cipher", "PROGRESS", f"Found {len(exa_results)} external sources via Exa.")
                
            except Exception as exa_e:
                print(f"[WARN] Exa failed: {exa_e}")
        
        # 3. AI Analysis (Weaver/Analyst Role)
        prompt = f"""
        You are an Investment Analyst and Tech Writer.
        
        Target URL: {url}
        
        [INTERNAL LANDING PAGE SCRAPE]:
        {raw_text[:6000]} (Truncated)
        
        [EXTERNAL MARKET CONTEXT (EXA)]:
        {exa_context}
        
        Task: Write a "Deep Dive" analysis of this product.
        
        Structure:
        1. **The Hook:** What is this? Why is it interesting?
        2. **Value Prop:** What problem does it solve?
        3. **Market Signal:** What are people/news saying? (Use Exa context if available)
        4. **Bull Case:** Why could this be huge?
        5. **Bear Case:** What are the risks?
        
        Tone: Professional, Insightful, "VC Twitter" style.
        Format: Markdown.
        """
        
        analysis = gateway.generate(prompt, "You are a top-tier tech analyst.")
        
        # 3. Generate HTML Report (Premium Style)
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
                h2 {{ color: #1e293b; margin-top: 30px; }}
                strong {{ color: #0f172a; }}
                .meta {{ font-size: 12px; color: #64748b; margin-bottom: 20px; }}
                .highlight {{ background: #f0f9ff; padding: 15px; border-left: 4px solid #0ea5e9; border-radius: 4px; margin: 20px 0; }}
                .screenshot {{ width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
                .footer {{ margin-top: 50px; font-size: 12px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="meta">GENERATED BY DEEP RESEARCH AI • {datetime.now().strftime('%B %d, %Y')}</div>
            <h1>Deep Dive: {url}</h1>
            
            <div class="highlight">
                <strong>Executive Summary:</strong>
                See attached screenshot for visual verification.
            </div>
            
            {analysis.replace('**', '<b>').replace('**', '</b>').replace('\n', '<br>')}
            
            <div class="footer">
                © 2026 INP Capital. Confidential & Proprietary.
            </div>
        </body>
        </html>
        """
        
        # Save Report
        report_path = f"{OUTPUT_DIR}/{site_name}_{timestamp}_Analysis.md"
        # We also save .html for debugging
        html_path = f"{OUTPUT_DIR}/{site_name}_{timestamp}_Report.html"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(analysis) # Keep raw MD
            
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"[SUCCESS] Reports saved: {report_path}, {html_path}")
        dc.post("cipher", "DONE", f"Research Complete. Generated HTML Report.")
        
        # Email Logic
        if target_email:
            print(f"[EMAIL] Sending Premium Report to {target_email}...")
            
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
            email_script = os.path.join(root_dir, "skills/smtp-send/scripts/send_email.py")
            
            # Send HTML body + Attach Screenshot + Attach Markdown
            email_cmd = [
                "python", email_script,
                "--to", target_email,
                "--subject", f"🎯 Deep Dive: {site_name}",
                "--body", html_content, 
                "--html", # Enable HTML flag
                "--attachment", screenshot_path,
                "--attachment", report_path
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
