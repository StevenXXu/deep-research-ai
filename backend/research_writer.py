import os
import sys
import json
import time
import shutil
from datetime import datetime
import subprocess
from dotenv import load_dotenv

# Add Root to Path
# This is required to import llm_gateway and find .env
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(root_dir)

from llm_gateway import gateway
from email_sender import send_email # Local module
import discord_connector as dc
from exa_py import Exa
import markdown
from research_engine import ResearchEngine # NEW
import subprocess

# Add root to path to find consult_notebooklm
sys.path.append(os.path.abspath(os.path.join(root_dir)))
try:
    import consult_notebooklm
except ImportError:
    consult_notebooklm = None

# Deep Research Writer
# 1. Navigates to a URL (Playwright)
# 2. Uses ResearchEngine (Exa/Tavily/Brave + LLM)
# 3. Generates "Investment Grade" Analysis

OUTPUT_DIR = "workspace/research_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load Keys from Root Env (Optional - Railway injects envs automatically)
# IMPORTANT: override=False ensures we don't overwrite system envs with empty .env values
load_dotenv(os.path.join(root_dir, ".env"), override=False)
NOTEBOOK_ID = os.getenv("NOTEBOOK_ID") # For Deal Flow Memory

def run_research(url, target_email=None, document_text=None, progress_callback=None):
    def update_status(progress, status):
        if progress_callback:
            progress_callback(progress, status)
        print(f"[RESEARCH] {progress}% - {status}")

    update_status(5, f"Initializing research on {url}...")
    dc.post("cipher", "START", f"Starting Deep Research (Premium) on {url}")
    
    timestamp = int(time.time())
    site_name = url.split("//")[-1].replace("/", "_")
    screenshot_path = os.path.abspath(f"{OUTPUT_DIR}/{site_name}_{timestamp}.png")
    
    # 0. Check Memory (NotebookLM)
    memory_context = ""
    if NOTEBOOK_ID and consult_notebooklm:
        update_status(10, "Querying Memory (NotebookLM)...")
        dc.post("cipher", "PROGRESS", "Querying NotebookLM for historical context...")
        query = f"What do we know about {site_name} or this sector? Have we looked at similar competitors?"
        memory_context = consult_notebooklm.query_notebooklm(query, notebook_id=NOTEBOOK_ID)
        print(f"[RESEARCH] Memory Context: {memory_context[:200]}...")

    # 1. Browser Automation (Screenshot + Text)
    # ... (Keep existing Playwright JS script generation) ...
    update_status(15, "Browsing Target Website...")
    js_script = f"""
    const {{ chromium }} = require('playwright');
    (async () => {{
      const browser = await chromium.launch();
      const page = await browser.newPage();
      try {{
        console.log("Navigating...");
        await page.goto('{url}', {{ waitUntil: 'domcontentloaded', timeout: 60000 }});
        await page.waitForTimeout(3000); 
        await page.screenshot({{ path: '{screenshot_path.replace(os.sep, "/")}', fullPage: false }}); 
        
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
        
    try:
        print("[RESEARCH] Browsing site...", flush=True)
        # Linux/Cloud-First Node Resolution
        node_exec = "node"
        if shutil.which("node"):
            node_exec = shutil.which("node")
            
        # Execute Scraper
        result = subprocess.run([node_exec, js_path], capture_output=True, text=True, encoding="utf-8")
        
        output = result.stdout
        # Ensure we capture errors if stdout is empty
        if result.returncode != 0:
             print(f"[WARN] Node script error: {result.stderr}", flush=True)

        raw_text = ""
        if "__CONTENT_START__" in output:
            raw_text = output.split("__CONTENT_START__")[1].split("__CONTENT_END__")[0]
        else:
            print(f"[WARN] Browser Output format mismatch. Raw output: {output[:200]}...", flush=True)
            
        print(f"[RESEARCH] Extracted landing page text.", flush=True)
        update_status(25, "Site Scraped. Engaging Research Engine...")
        dc.post("cipher", "PROGRESS", f"Scraped site. Screenshot saved.")

        # 2. Research Engine (The New Brain)
        update_status(30, "Phase 1: Broad Market Scan (Exa/Tavily)...")
        engine = ResearchEngine(url, document_content=document_text)
        
        # Inject Landing Page + Memory Context
        engine.sources.append({"title": "Landing Page", "url": url, "content": raw_text[:2000], "source": "Landing Page"})
        if memory_context:
            engine.sources.append({"title": "Internal Memory (NotebookLM)", "url": "internal", "content": memory_context, "source": "NotebookLM"})
        
        # Execute Phases 1-4
        engine.phase_1_broad_scan()
        
        update_status(50, "Phase 2: Identifying Knowledge Gaps...")
        engine.phase_2_gap_analysis()
        
        update_status(60, "Phase 3: Deep Dive (Apify/Social/Trends)...")
        engine.phase_3_deep_dive()
        
        update_status(80, "Phase 4: Synthesizing Investment Memo...")
        analysis = engine.phase_4_synthesis() # Returns Markdown Report

        # 3. Generate HTML Report (Premium Style)
        update_status(90, "Generating PDF Report...")
        # Convert Markdown to HTML
        # Pre-process: Fix common table formatting issues & Strip Filler
        import re
        
        # Strip Chatty Intro (Remove everything before the first Header #)
        if "# " in analysis:
            # Keep the header and everything after
            analysis = "# " + analysis.split("# ", 1)[1]
            
        # Fix: ensure |---| separator line exists and is clean
        analysis = re.sub(r'\| *:?-+:? *\|', lambda m: m.group(0).strip(), analysis) 
        
        # Convert
        analysis_html = markdown.markdown(
            analysis, 
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        
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
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }}
                th {{ background-color: #f3f4f6; font-weight: 600; }}
                strong {{ color: #111827; font-weight: 600; }}
                /* Table Styling */
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 24px 0; 
                    font-size: 14px; 
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
                    border-radius: 6px; 
                    overflow: hidden; 
                }}
                th {{ 
                    background-color: #f3f4f6; 
                    color: #374151; 
                    font-weight: 700; 
                    text-transform: uppercase; 
                    font-size: 11px; 
                    letter-spacing: 0.5px; 
                    padding: 12px 16px; 
                    text-align: left; 
                    border-bottom: 2px solid #e5e7eb; 
                }}
                td {{ 
                    border-bottom: 1px solid #f3f4f6; 
                    padding: 12px 16px; 
                    color: #4b5563; 
                    vertical-align: top;
                }}
                tr:last-child td {{ border-bottom: none; }}
                tr:nth-child(even) {{ background-color: #f9fafb; }}
                
                .meta {{ font-size: 11px; font-weight: 600; letter-spacing: 1px; color: #6b7280; text-transform: uppercase; margin-bottom: 8px; }}
                .hero {{ width: 100%; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 32px; }}
                .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #9ca3af; }}
                .ref {{ font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 40px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="meta">CONFIDENTIAL • DEEP RESEARCH MEMO</div>
                <h1>{site_name}</h1>
                
                <img src="cid:screenshot" class="hero" alt="Landing Page Screenshot">
                
                {analysis_html}
                
                <div class="footer">
                    Generated by Deep Research AI (Premium) • {datetime.now().strftime('%Y-%m-%d')}
                </div>
            </div>
        </body>
        </html>
        """
        
        # Save Report
        report_path = f"{OUTPUT_DIR}/{site_name}_{timestamp}_Analysis.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(analysis) 
            
        # 4. Generate PDF (DISABLED TEMPORARILY to fix flow)
        pdf_path = None
        # pdf_path = f"{OUTPUT_DIR}/{site_name}_{timestamp}_Memo.pdf"
        # try:
        #     print("[RESEARCH] Generating PDF via Playwright...")
        #     # ... (PDF generation code commented out) ...
        # except Exception as pdf_e:
        #     print(f"[WARN] PDF Gen failed: {pdf_e}")
        #     pdf_path = None

        print(f"[SUCCESS] Reports saved: {report_path}")
        dc.post("cipher", "DONE", f"Research Complete. Generated Premium Report.")
        
        # Email Logic
        if target_email:
            update_status(95, f"Sending Email to {target_email}...")
            
            # Debug: Verify Credentials loaded (Masked)
            email_user = os.getenv("EMAIL_USER", "")
            masked_user = email_user[:3] + "***" + email_user.split('@')[-1] if email_user else "NONE"
            print(f"[EMAIL] Using Creds: {masked_user}", flush=True)

            print(f"[EMAIL] Sending Premium Report to {target_email}...", flush=True)
            
            inline_images = []
            if os.path.exists(screenshot_path):
                inline_images.append((screenshot_path, "screenshot"))
            
            attachments = []
            if os.path.exists(report_path):
                attachments.append(report_path)
            if pdf_path and os.path.exists(pdf_path):
                attachments.append(pdf_path)

            success = send_email(
                to_addr=target_email,
                subject=f"📋 Prescreen Memo with deep research: {site_name}",
                body=html_content,
                is_html=True,
                attachments=attachments,
                inline_images=inline_images
            )
            
            if success:
                print(f"[EMAIL] Sent successfully.", flush=True)
            else:
                update_status(99, "Email failed. Uploading report to Discord backup.")
                # Fallback: Upload File to Discord
                dc.post("cipher", "ERROR", f"Email failed (Network/Auth). Uploading report directly:", file_path=report_path)
        
        update_status(100, "Done! Check your email or Discord.")
        try:
            os.remove(js_path)
        except:
            pass
        return report_path

    except Exception as e:
        update_status(0, f"Error: {str(e)}")
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
