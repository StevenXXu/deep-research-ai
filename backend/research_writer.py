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
        
        # Clean Site Name for Title (e.g. "www.breaker.com" -> "Breaker")
        display_title = site_name
        if "www." in site_name:
            display_title = site_name.replace("www.", "")
        if "." in display_title:
            display_title = display_title.split(".")[0]
        display_title = display_title.replace("_", " ").title()

        # Convert Markdown to HTML
        import re
        if "# " in analysis:
            analysis = "# " + analysis.split("# ", 1)[1]
        analysis = re.sub(r'\| *:?-+:? *\|', lambda m: m.group(0).strip(), analysis) 
        
        analysis_html = markdown.markdown(
            analysis, 
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        
        # CSS for PDF/Email
        # Added page-break rules for PDF
        css_style = """
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1f2937; max-width: 800px; margin: 0 auto; padding: 40px; background-color: #ffffff; }
                .container { background: #ffffff; padding: 0; }
                h1 { font-size: 28px; font-weight: 800; color: #111827; border-bottom: 4px solid #000; padding-bottom: 16px; margin-bottom: 32px; letter-spacing: -0.5px; }
                h2 { font-size: 20px; font-weight: 700; color: #374151; margin-top: 40px; margin-bottom: 16px; page-break-after: avoid; border-left: 4px solid #3b82f6; padding-left: 12px; }
                p { margin-bottom: 16px; color: #4b5563; text-align: justify; }
                ul { margin-bottom: 16px; padding-left: 20px; }
                li { margin-bottom: 8px; }
                
                /* Table Styling - Robust for PDF */
                table { 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 24px 0; 
                    font-size: 13px; 
                    border: 1px solid #e5e7eb;
                    page-break-inside: avoid; /* Prevent table splitting */
                }
                th { 
                    background-color: #f9fafb; 
                    color: #111827; 
                    font-weight: 700; 
                    text-transform: uppercase; 
                    font-size: 11px; 
                    padding: 12px; 
                    text-align: left; 
                    border-bottom: 2px solid #e5e7eb; 
                }
                td { 
                    border-bottom: 1px solid #e5e7eb; 
                    padding: 12px; 
                    color: #4b5563; 
                    vertical-align: top;
                }
                tr:last-child td { border-bottom: none; }
                tr:nth-child(even) { background-color: #fcfcfc; }
                
                .meta { font-size: 10px; font-weight: 700; letter-spacing: 1.5px; color: #9ca3af; text-transform: uppercase; margin-bottom: 16px; display: block; }
                .hero { width: 100%; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 32px; max-height: 400px; object-fit: cover; }
                .footer { margin-top: 60px; text-align: center; font-size: 11px; color: #d1d5db; border-top: 1px solid #f3f4f6; padding-top: 20px; }
        """

        # Template Base
        def render_html(img_src):
            return f"""
            <html>
            <head><style>{css_style}</style></head>
            <body>
                <div class="container">
                    <span class="meta">CONFIDENTIAL • PRE-SCREEN MEMO</span>
                    <h1>{display_title}</h1>
                    <img src="{img_src}" class="hero" alt="Landing Page Screenshot">
                    {analysis_html}
                    <div class="footer">
                        Generated by Deep Research AI • {datetime.now().strftime('%Y-%m-%d')}
                    </div>
                </div>
            </body>
            </html>
            """

        # 1. Email Version (cid:screenshot)
        email_html = render_html("cid:screenshot")
        
        # 2. PDF Version (Local Path for Playwright)
        # Playwright needs absolute path with file:// protocol or just absolute path depending on OS
        # Using forward slashes is safest for file:// URLs
        abs_screenshot_path = screenshot_path.replace(os.sep, "/")
        pdf_html = render_html(f"file://{abs_screenshot_path}")
            
        # Save Markdown Report (Keep original logic)
        report_path = f"{OUTPUT_DIR}/{site_name}_{timestamp}_Analysis.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(analysis) 
            
        # 4. Generate PDF
        pdf_path = f"{OUTPUT_DIR}/{site_name}_{timestamp}_Memo.pdf"
        try:
            update_status(92, "Generating PDF...")
            print("[RESEARCH] Generating PDF via Playwright...", flush=True)
            
            temp_html_path = os.path.abspath(f"{OUTPUT_DIR}/{site_name}_{timestamp}_temp.html")
            with open(temp_html_path, "w", encoding="utf-8") as f:
                f.write(pdf_html) # Use the PDF-specific HTML
                
            pdf_script = f"""
            const {{ chromium }} = require('playwright');
            (async () => {{
              const browser = await chromium.launch();
              const page = await browser.newPage();
              try {{
                  await page.goto('file://{temp_html_path.replace(os.sep, "/")}', {{ waitUntil: 'networkidle' }});
                  await page.pdf({{ 
                    path: '{pdf_path.replace(os.sep, "/")}', 
                    format: 'A4', 
                    printBackground: true, 
                    margin: {{ top: '2cm', bottom: '2cm', left: '2cm', right: '2cm' }} 
                  }});
              }} finally {{
                  await browser.close();
              }}
            }})();
            """
            
            pdf_js_path = f"{OUTPUT_DIR}/temp_pdf_gen_{timestamp}.js"
            with open(pdf_js_path, "w", encoding="utf-8") as f:
                f.write(pdf_script)
            
            # Resolve Node
            node_exec = "node"
            if shutil.which("node"):
                node_exec = shutil.which("node")

            result = subprocess.run([node_exec, pdf_js_path], capture_output=True, text=True, encoding="utf-8")
            
            if result.returncode != 0:
                print(f"[WARN] PDF Gen failed: {result.stderr}", flush=True)
                pdf_path = None
            else:
                print(f"[SUCCESS] PDF Generated: {pdf_path}", flush=True)
            
            # Clean up temp files
            try:
                os.remove(temp_html_path)
                os.remove(pdf_js_path)
            except:
                pass
                
        except Exception as pdf_e:
            print(f"[WARN] PDF Gen Exception: {pdf_e}", flush=True)
            pdf_path = None

        print(f"[SUCCESS] Reports saved: {report_path}", flush=True)
        dc.post("cipher", "DONE", f"Research Complete. Generated Premium Report.")
        
        # Email Logic
        if target_email:
            update_status(95, f"Sending Email to {target_email}...")
            
            # Debug: Verify Resend Key loaded
            resend_key = os.getenv("RESEND_API_KEY", "")
            masked_key = resend_key[:3] + "***" if resend_key else "NONE"
            print(f"[EMAIL] Auth Provider: Resend (Key: {masked_key})", flush=True)

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
                subject=f"📋 Pre-Screen Memo: {display_title}",
                body=email_html, # Use the Email-specific HTML
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
