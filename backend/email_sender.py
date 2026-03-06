import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from dotenv import load_dotenv

# Env vars from Railway Variables
SMTP_SERVER = os.getenv("EMAIL_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("EMAIL_PORT", 587))
USER = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(to_addr, subject, body, is_html=False, attachments=None, inline_images=None):
    if not USER or not PASSWORD:
        print("[ERROR] EMAIL_USER or EMAIL_PASSWORD not set in environment.")
        return False

    msg = MIMEMultipart('mixed')
    msg['From'] = USER
    msg['To'] = to_addr
    msg['Subject'] = subject

    # Handle Body + Inline Images (Related) or just Body (Alternative)
    if inline_images:
        msg_related = MIMEMultipart('related')
        msg.attach(msg_related)
        
        msg_alternative = MIMEMultipart('alternative')
        msg_related.attach(msg_alternative)
        msg_alternative.attach(MIMEText(body, 'html' if is_html else 'plain'))
        
        for fpath, cid in inline_images:
            if os.path.exists(fpath):
                try:
                    with open(fpath, 'rb') as f:
                        img = MIMEImage(f.read())
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(fpath))
                    msg_related.attach(img)
                except Exception as e:
                    print(f"[WARN] Failed to attach inline image {fpath}: {e}")
    else:
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(body, 'html' if is_html else 'plain'))

    # Attachments
    if attachments:
        for fpath in attachments:
            if os.path.exists(fpath):
                try:
                    with open(fpath, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(fpath))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(fpath)}"'
                    msg.attach(part)
                except Exception as e:
                    print(f"[WARN] Failed to attach file {fpath}: {e}")

    try:
        # Use SSL (465) instead of STARTTLS (587) for better stability with some Gmail configs
        # or properly handle the EHLO for 587
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.ehlo()
            server.starttls()
            server.ehlo()
            
        server.login(USER, PASSWORD)
        server.sendmail(USER, to_addr, msg.as_string())
        server.quit()
        print(f"[SUCCESS] Email sent to {to_addr}", flush=True)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}", flush=True)
        return False
