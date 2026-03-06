import os
import resend
from dotenv import load_dotenv

# Load Env
load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "onboarding@resend.dev") # Default Resend test sender

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

def send_email(to_addr, subject, body, is_html=False, attachments=None, inline_images=None):
    """
    Sends email via Resend API (HTTP).
    Robust, fast, and firewall-friendly.
    """
    if not RESEND_API_KEY:
        print("[ERROR] RESEND_API_KEY not set. Cannot send email.", flush=True)
        return False

    print(f"[EMAIL] Sending via Resend API to {to_addr}...", flush=True)

    params = {
        "from": EMAIL_FROM,
        "to": [to_addr],
        "subject": subject,
        "html" if is_html else "text": body,
    }

    # Handle Attachments
    # Resend expects attachments as a list of dicts:
    # { "filename": "report.md", "content": [list of bytes] }
    if attachments:
        att_list = []
        for fpath in attachments:
            if os.path.exists(fpath):
                try:
                    with open(fpath, "rb") as f:
                        # Resend Python SDK handles file reading if we pass bytes
                        # Actually, looking at docs, it needs 'content' as list of integers (bytes)
                        # OR simply 'path'??
                        # The safest way per docs is reading content.
                        content_bytes = f.read()
                        # Convert bytes to list of integers for JSON serialization if needed,
                        # BUT the official SDK usually takes bytes or lists.
                        # Let's check typical usage.
                        att_list.append({
                            "filename": os.path.basename(fpath),
                            "content": list(content_bytes) 
                        })
                except Exception as e:
                    print(f"[WARN] Failed to read attachment {fpath}: {e}", flush=True)
        
        if att_list:
            params["attachments"] = att_list

    try:
        r = resend.Emails.send(params)
        # Check if 'id' is in response
        if r and r.get("id"):
            print(f"[SUCCESS] Email sent via Resend. ID: {r['id']}", flush=True)
            return True
        else:
            print(f"[ERROR] Resend API Response invalid: {r}", flush=True)
            return False
            
    except Exception as e:
        print(f"[ERROR] Resend API Failed: {e}", flush=True)
        return False
