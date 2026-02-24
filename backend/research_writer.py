import os
import sys
import json
import time
from datetime import datetime
import subprocess
from dotenv import load_dotenv

# Add Root to Path
# This is required to import llm_gateway and find .env
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(root_dir)

from llm_gateway import gateway
import discord_connector as dc
from exa_py import Exa
import markdown

# Deep Research Writer
# 1. Navigates to a URL (Playwright)
# 2. Searches for Context (Exa)
# 3. Generates "Investment Grade" Analysis

OUTPUT_DIR = "workspace/research_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load Exa Key from Root Env
load_dotenv(os.path.join(root_dir, ".env"))
EXA_KEY = os.getenv("EXA_API_KEY")

def run_research(url, target_email=None):
    print(f"[RESEARCH] Analyzing: {url}")
    dc.post("cipher", "START", f"Starting Deep Research on {url}")
    
    timestamp = int(time.time())
    site_name = url.split("//")[-1].replace("/", "_")
    screenshot_path = os.path.abspath(f"{OUTPUT_DIR}/{site_name}_{timestamp}.png")
    
    # 1. Browser Automation
    js_script = f"""
    const {{ chromium }} = require('playwright');

    (async () => {{
      const browser = await chromium.launch();
      const page = await browser.newPage();
      try {{
        console.log("Navigating...");
        await page.goto('{url}', {{ waitUntil: 'domcontentloaded', timeout: 60000 }});
        await page.waitForTimeout(3000); // Wait for JS hydration
        
        console.log("Screenshotting...");
        await page.screenshot({{ path: '{screenshot_path.replace(os.sep, "/")}', fullPage: false }}); // Capture Fold only for cleaner email
        
        // Extract Text + Meta
        const title = await page.title();
        const metaDesc = await page.$eval("meta[name='description']", element => element.content).catch(() => "");
        const content = await page.innerText('body');
        
        console.log("__CONTENT_START__");
        console.log("Title: " + title);
        console.log("Meta: " + metaDesc);
        console.log("\\n" + content);
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
                # Removing use_autoprompt as it caused error in SDK 2.4.0
                search_response = exa.search_and_contents(
                    f"{domain} startup funding competitors news",
                    type="neural",
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
        
        # 3. AI Analysis
        prompt = f"""
        You are a VC Associate writing a "Deck Prescreener" memo.
        
        Target URL: {url}
        
        [LANDING PAGE DATA]:
        {raw_text[:8000]}
        
        [MARKET INTELLIGENCE]:
        {exa_context}
        
        Task: Write a structured Investment Memo.
        Style: High conviction, dense information, no fluff.
        
        Structure:
        # One-Liner
        (A single sentence describing the company)
        
        ## 1. Problem & Solution
        (What is the pain point? How do they solve it?)
        
        ## 2. Market Opportunity
        (Who buys this? Competitors? Market size?)
        
        ## 3. Traction & Signals
        (Any news, funding, or user reviews found?)
        
        ## 4. Verdict
        (Bull/Bear case summary)
        """
        
        analysis = gateway.generate(prompt, "You are a VC analyst.")
        
        # Convert Markdown to HTML
        analysis_html = markdown.markdown(analysis)
        
        # 3. Generate HTML Report (Premium Style)
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1f2937; max-width: 800px; margin: 0 auto; padding: 40px; background-color: #f9fafb; }}
                .container {{ background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
                h1 {{ font-size: 24px; font-weight: 800; color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 16px; margin-bottom: 24px; }}
                h2 {{ font-size: 18px; font-weight: 700; color: #374151; margin-top: 32px; margin-bottom: 12px; }}
                p {{ margin-bottom: 16px; color: #4b5563; }}
                ul {{ margin-bottom: 16px; padding-left: 20px; }}
                li {{ margin-bottom: 8px; }}
                strong {{ color: #111827; font-weight: 600; }}
                .meta {{ font-size: 11px; font-weight: 600; letter-spacing: 1px; color: #6b7280; text-transform: uppercase; margin-bottom: 8px; }}
                .hero {{ width: 100%; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 32px; }}
                .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #9ca3af; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="meta">CONFIDENTIAL • PRE-SCREEN MEMO</div>
                <h1>{site_name}</h1>
                
                <img src="cid:screenshot" class="hero" alt="Landing Page Screenshot">
                
                {analysis_html}
                
                <div class="footer">
                    Generated by Deep Research AI • {datetime.now().strftime('%Y-%m-%d')}
                </div>
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
            
            # Send HTML body + Inline Screenshot
            # Format for inline: "path|cid" (Pipe separator for Windows safety)
            inline_arg = f"{screenshot_path}|screenshot"
            
            email_cmd = [
                "python", email_script,
                "--to", target_email,
                "--subject", f"🎯 Deep Dive: {site_name}",
                "--body", html_content, 
                "--html", 
                "--inline", inline_arg,
                "--attachment", report_path # Keep MD as backup attachment
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
