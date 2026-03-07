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

    # Handle Inline Images (Add to attachments with content_id)
    if inline_images:
        if not attachments: attachments = []
        for fpath, cid in inline_images:
            if os.path.exists(fpath):
                # We treat inline images as attachments with a specific content_id
                # This allows Resend to map <img src="cid:..."> correctly if supported
                # NOTE: Resend Python SDK might not fully support 'content_id' in all versions
                # If this fails, the image just becomes a regular attachment.
                pass 
                # Actually, let's just merge them into the attachment loop below
                # but we need to track the CID.
    
    # Process Attachments (Standard + Inline)
    final_attachments = []
    
    # 1. Standard Attachments
    if attachments:
        for fpath in attachments:
            if os.path.exists(fpath):
                try:
                    with open(fpath, "rb") as f:
                        content_bytes = f.read()
                        final_attachments.append({
                            "filename": os.path.basename(fpath),
                            "content": list(content_bytes) 
                        })
                except Exception as e:
                    print(f"[WARN] Failed to read attachment {fpath}: {e}", flush=True)

    # 2. Inline Images (Screenshot)
    if inline_images:
        for fpath, cid in inline_images:
            if os.path.exists(fpath):
                try:
                    with open(fpath, "rb") as f:
                        content_bytes = f.read()
                        # Resend allows 'content_id' (or 'content_id' in some docs? Let's try standard)
                        # Official Resend docs use 'content_id' for inline images.
                        final_attachments.append({
                            "filename": os.path.basename(fpath),
                            "content": list(content_bytes),
                            "content_id": cid  # This enables <img src="cid:screenshot">
                        })
                except Exception as e:
                    print(f"[WARN] Failed to read inline image {fpath}: {e}", flush=True)

    if final_attachments:
        params["attachments"] = final_attachments

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
