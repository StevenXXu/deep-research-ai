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
# DISABLED: load_dotenv to prevent interference with Railway Variables
# load_dotenv(os.path.join(root_dir, ".env"), override=False)
NOTEBOOK_ID = os.getenv("NOTEBOOK_ID") # For Deal Flow Memory

# Initialize Supabase (Robust)
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

# Load from Railway System Envs ONLY (Skip .env file to avoid confusion)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") # Must use SERVICE_KEY

supabase: Client = None

print(f"[INIT] Checking Supabase Config...", flush=True)
if SUPABASE_URL:
    print(f"[INIT] URL Found: {SUPABASE_URL[:10]}...", flush=True)
else:
    print(f"[INIT] ERROR: SUPABASE_URL is Missing!", flush=True)

if SUPABASE_KEY:
    print(f"[INIT] KEY Found: {SUPABASE_KEY[:5]}...", flush=True)
else:
    print(f"[INIT] ERROR: SUPABASE_SERVICE_KEY is Missing!", flush=True)

if SUPABASE_URL and SUPABASE_KEY:
    try:
        # Use simple dict for options (Compatible with older and newer SDKs)
        # Or just default init if timeouts aren't critical
        # opts = ClientOptions().replace(postgrest_client_timeout=10) <--- Caused error
        
        # Fallback: Just init simply. The default timeout is usually fine.
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # If we really need timeout, we can try accessing postgrest client later
        if hasattr(supabase, "postgrest"):
            supabase.postgrest.timeout = 10
            
        print(f"[INIT] Supabase connected successfully.", flush=True)
    except Exception as e:
        print(f"[WARN] Supabase init failed: {e}", flush=True)
else:
    print(f"[WARN] Supabase init skipped due to missing vars.", flush=True)

def run_research(url, target_email=None, document_text=None, progress_callback=None, user_id=None, report_id=None, language="English"):
    def update_status(progress, status):
        if progress_callback:
            progress_callback(progress, status)
        print(f"[RESEARCH] {progress}% - {status}", flush=True)
        # SUPABASE REALTIME SYNC (Optional, but great UX)
        if supabase and report_id:
            try:
                # Update progress using a regular update. 
                # Avoid touching 'meta' column here if it doesn't exist in schema yet.
                supabase.table('reports').update({
                    "status": f"processing:{progress}"
                }).eq('id', report_id).execute()
            except Exception as e:
                # Silently fail progress updates to avoid crashing the main run
                pass

    # Helper: Save to DB
    def save_history(status, content=None, meta=None):
        if not supabase:
            print("[DB] Supabase client not active. Skipping save.", flush=True)
            return
        if not user_id: 
            print("[DB] No user_id provided. Skipping save.", flush=True)
            return
            
        try:
            print(f"[DB] Saving/Updating report for user {user_id}...", flush=True)
            
            # REFUND LOGIC: If status is failed, refund 1 credit
            if status == "failed":
                try:
                    # 1. Fetch current credits
                    print(f"[DB] Initiating refund for user {user_id}...", flush=True)
                    user_res = supabase.table("profiles").select("credits_remaining").eq("user_id", user_id).single().execute()
                    current_credits = user_res.data.get("credits_remaining", 0)
                    # 2. Add 1 credit back
                    supabase.table("profiles").update({"credits_remaining": current_credits + 1}).eq("user_id", user_id).execute()
                    print(f"[DB] Refund successful. Credits restored to {current_credits + 1}.", flush=True)
                except Exception as refund_e:
                    print(f"[DB-ERROR] Failed to refund credit: {refund_e}", flush=True)

            data = {
                "user_id": user_id,
                "target_url": url,
                "status": status,
                "created_at": datetime.utcnow().isoformat(),
            }
            if content:
                data["report_content"] = content
                
            # Add Metadata if available
            if meta:
                # Merge existing meta fields
                if "company_name" in meta: data["company_name"] = meta.get("company_name")
                if "sector_tags" in meta: data["sector_tags"] = meta.get("sector_tags")
                if "cost_usd" in meta: data["cost_usd"] = meta.get("cost_usd")
                
            # Perform Update if report_id exists, else Insert
            try:
                if report_id:
                    res = supabase.table("reports").update(data).eq("id", report_id).execute()
                    print(f"[DB] Updated existing report {report_id} to status: {status}.", flush=True)
                else:
                    res = supabase.table("reports").insert(data).execute()
                    print(f"[DB] Inserted new report to history.", flush=True)
            except Exception as e:
                # Handle Foreign Key Violation (Missing Profile)
                if "foreign key constraint" in str(e) or "23503" in str(e):
                    print(f"[DB] Missing Profile for {user_id}. Creating fallback profile...", flush=True)
                    # Create minimal profile
                    profile_data = {
                        "user_id": user_id,
                        "email": target_email or "unknown@email.com",
                        "full_name": "User (Auto-Created)",
                        "credits_remaining": 1 # Default 1 Credit (adjusted)
                    }
                    supabase.table("profiles").insert(profile_data).execute()
                    print(f"[DB] Fallback profile created. Retrying report save...", flush=True)
                    # Retry Report Update/Insert
                    if report_id:
                        supabase.table("reports").update(data).eq("id", report_id).execute()
                    else:
                        supabase.table("reports").insert(data).execute()
                    print(f"[DB] Saved report on retry.", flush=True)
                else:
                    raise e
            
        except Exception as e:
            print(f"[DB] Error saving history: {e}", flush=True)

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

    # 1. Web Extraction (Using Scrapling instead of Node.js Playwright for stealth)
    update_status(15, "Browsing Target Website (Scrapling)...")
    raw_text = ""
    
    # Take screenshot in an isolated subprocess to avoid asyncio Event Loop conflicts in Threads
    try:
        print("[RESEARCH] Taking screenshot using isolated subprocess...", flush=True)
        py_script = f"""
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('{url}', wait_until="domcontentloaded", timeout=45000)
        page.screenshot(path='{screenshot_path.replace(os.sep, "/")}', full_page=False)
        browser.close()
except Exception as e:
    print("Screenshot error:", e)
"""
        py_path = f"{OUTPUT_DIR}/temp_screenshot_{timestamp}.py"
        with open(py_path, "w", encoding="utf-8") as f:
            f.write(py_script)
            
        import subprocess
        subprocess.run([sys.executable, py_path], capture_output=True, text=True, timeout=60)
        try:
            os.remove(py_path)
        except:
            pass
            
        if os.path.exists(screenshot_path):
            print(f"[RESEARCH] Screenshot saved successfully.", flush=True)
        else:
            print(f"[WARN] Screenshot file was not created.", flush=True)
            
    except Exception as se:
        print(f"[WARN] Screenshot subprocess failed: {se}", flush=True)

    try:
        from scrapling.fetchers import StealthyFetcher
        print("[RESEARCH] Browsing site using Scrapling StealthyFetcher...", flush=True)
        # Using stealthy fetcher to bypass Cloudflare and get content
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
        raw_text = page.css('body::text').getall()
        raw_text = " ".join([t.strip() for t in raw_text if t.strip()])
        print(f"[RESEARCH] Extracted landing page text.", flush=True)
        
    except Exception as e:
        print(f"[WARN] Scrapling failed: {e}. Falling back to basic requests.", flush=True)
        try:
            import requests
            from bs4 import BeautifulSoup
            res = requests.get(url, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")
            raw_text = soup.get_text(separator=" ", strip=True)
        except Exception as e2:
            print(f"[WARN] Fallback failed: {e2}", flush=True)
            
    update_status(25, "Site Scraped. Engaging Research Engine...")
    dc.post("cipher", "PROGRESS", f"Scraped site. Screenshot saved.")

    try:
        # 2. Research Engine (The New Brain)
        update_status(30, "Phase 1: Broad Market Scan...")
        engine = ResearchEngine(url, document_content=document_text, language=language)
        
        # Inject Landing Page + Memory Context
        engine.sources.append({"title": "Landing Page", "url": url, "content": raw_text[:2000], "source": "Landing Page"})
        if memory_context:
            engine.sources.append({"title": "Internal Memory (NotebookLM)", "url": "internal", "content": memory_context, "source": "NotebookLM"})
        
        # Execute Phases 1-4
        engine.phase_1_broad_scan()
        
        update_status(50, "Phase 2: Identifying Knowledge Gaps...")
        engine.phase_2_gap_analysis()
        
        update_status(60, "Phase 3: Deep Dive (Social/Trends)...")
        engine.phase_3_deep_dive()
        
        update_status(80, "Phase 4: Synthesizing Native Investment Memo...")
        analysis = engine.phase_4_synthesis() # Returns Markdown Report

        # 3. Generate HTML Report (Premium Style)
        update_status(90, "Generating PDF Report...")
        
        # Clean Site Name for Title (e.g. "www.breaker.com" -> "Breaker")
        display_title = site_name
        if "www." in site_name:
            display_title = site_name.replace("www.", "")
        if "." in display_title:
            display_title = display_title.split(".")[0]
        # Clean hyphens and underscores
        display_title = display_title.replace("_", " ").replace("-", " ").title()

        # Convert Markdown to HTML
        import re
        
        # 1. Smart Title Stripping: Remove the first H1 header and anything before it
        # This fixes "Zipline # Zipline Investment Memo" double title issues
        # Pattern: Start of string -> any text (lazy) -> # Header -> Newline
        analysis = re.sub(r'^.*?# [^\n]+\n', '', analysis, flags=re.DOTALL).strip()
        
        # 2. Table Formatting Fix: Aggressively ensure blank line before tables
        # Strategy: Split by lines. If a line starts with | and prev line is not empty and not a table row, insert empty line.
        lines = analysis.split('\n')
        cleaned_lines = []
        for i, line in enumerate(lines):
            # Header Number Stripping (e.g. "## 1. Exec" -> "## Exec")
            if line.strip().startswith('#'):
                line = re.sub(r'^(#+)\s*\d+\.\s*', r'\1 ', line)
                
            # Table Fix logic
            if line.strip().startswith('|'):
                # If it's a table row
                if i > 0:
                    prev_line = lines[i-1].strip()
                    # If prev line is text (not empty, not table, not header), insert gap
                    if prev_line and not prev_line.startswith('|') and not prev_line.startswith('#'):
                        cleaned_lines.append('')
            
            cleaned_lines.append(line)
            
        analysis = '\n'.join(cleaned_lines)
        
        # 3. Clean Pipe Tables (Standardize spacing)
        analysis = re.sub(r'\| *:?-+:? *\|', lambda m: m.group(0).strip(), analysis) 
        
        # 4. Remove ugly HTML <br> tags sometimes generated by LLMs in tables
        analysis = analysis.replace('<br>', '').replace('<br/>', '').replace('<br />', '')

        analysis_html = markdown.markdown(
            analysis, 
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        
        # CSS for PDF/Email
        # Added page-break rules for PDF + Link Styling
        css_style = """
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1f2937; max-width: 800px; margin: 0 auto; padding: 40px; background-color: #ffffff; }
                .container { background: #ffffff; padding: 0; }
                h1 { font-size: 28px; font-weight: 800; color: #111827; border-bottom: 4px solid #000; padding-bottom: 16px; margin-bottom: 32px; letter-spacing: -0.5px; }
                h2 { font-size: 20px; font-weight: 700; color: #374151; margin-top: 40px; margin-bottom: 16px; page-break-after: avoid; border-left: 4px solid #3b82f6; padding-left: 12px; }
                p { margin-bottom: 16px; color: #4b5563; text-align: justify; }
                ul { margin-bottom: 16px; padding-left: 20px; }
                li { margin-bottom: 8px; }
                a { color: #2563eb; text-decoration: underline; } /* Blue Links */
                
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
            img_tag = f'<img src="{img_src}" class="hero" alt="Landing Page Screenshot">' if img_src else ''
            return f"""
            <html>
            <head><style>{css_style}</style></head>
            <body>
                <div class="container">
                    <span class="meta">CONFIDENTIAL • PRE-SCREEN MEMO</span>
                    <h1>{display_title}</h1>
                    {img_tag}
                    {analysis_html}
                    <div class="footer">
                        Generated by SoloAnalyst • {datetime.now().strftime('%Y-%m-%d')}
                    </div>
                </div>
            </body>
            </html>
            """

        # 1. Email Version (cid:screenshot)
        email_html = render_html("cid:screenshot" if os.path.exists(screenshot_path) else "")
        
        # 2. PDF Version (Local Path for Playwright)
        # Playwright needs absolute path with file:// protocol or just absolute path depending on OS
        # Using forward slashes is safest for file:// URLs
        abs_screenshot_path = screenshot_path.replace(os.sep, "/")
        pdf_html = render_html(f"file://{abs_screenshot_path}" if os.path.exists(screenshot_path) else "")
            
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

        # 5. Metadata & Cost Calculation (For Admin Dashboard)
        update_status(95, "Finalizing Metadata...")
        meta = engine.extract_metadata(analysis)
        meta["cost_usd"] = engine.calculate_cost()
        
        print(f"[SUCCESS] Reports saved: {report_path}", flush=True)
        dc.post("cipher", "DONE", f"Research Complete. Cost: ${meta['cost_usd']}. Company: {meta.get('company_name')}")
        
        # Save to Supabase (With new Meta fields)
        # We save "completed" here, but we MUST make sure update_status doesn't overwrite it!
        save_history("completed", analysis, meta=meta)
        
        # Email Logic
        if target_email:
            # DO NOT call update_status() here with progress updates, because update_status 
            # blindly sets status back to 'processing:95', wiping out 'completed'.
            print(f"[EMAIL] Sending Email to {target_email}...", flush=True)
            
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
                print("[EMAIL] Email failed. Uploading report to Discord backup.", flush=True)
                # Fallback: Upload File to Discord
                dc.post("cipher", "ERROR", f"Email failed (Network/Auth). Uploading report directly:", file_path=report_path)
        
        # Don't call update_status(100) because it overwrites 'completed' in Supabase with 'processing:100'
        print("[RESEARCH] Done! Check your email or Discord.", flush=True)
        try:
            os.remove(js_path)
        except:
            pass
        return report_path

    except Exception as e:
        update_status(0, f"Error: {str(e)}")
        print(f"[ERROR] Research failed: {e}")
        dc.post("cipher", "ERROR", f"Research failed: {e}")
        save_history("failed")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        email = None
        if len(sys.argv) > 2:
            email = sys.argv[2]
        run_research(target_url, email)
    else:
        print("Usage: python research_writer.py <url> [email]")
