import sys
import json
import os
import requests
from dotenv import load_dotenv

# Load Env (to access Webhook URLs)
# Assumes this script is in root or PYTHONPATH allows finding .env
load_dotenv(".env")

# --- CONFIG: Webhook Map ---
# Maps agent/function names to Environment Variable Names
WEBHOOK_ENV_MAP = {
    # Core Agents
    "scout": "WEBHOOK_MARKET_INTEL",
    "analyst": "WEBHOOK_DEAL_FLOW",
    "echo": "WEBHOOK_SOCIAL_MONITOR",
    "broker": "WEBHOOK_TRADING_SIGNALS",
    "quill": "WEBHOOK_CONTENT_DRAFTS",
    "overseer": "WEBHOOK_PORTFOLIO_OPS",
    "weaver": "WEBHOOK_NOVEL_CREATION",
    "alfred": "WEBHOOK_SYSTEM_HEALTH",
    "cipher": "WEBHOOK_DEV_LAB",
    "spark": "WEBHOOK_FLASH_IDEAS",
    "archivist": "WEBHOOK_KNOWLEDGE_BASE", # Mapped to new env var

    # Specific Functions/Channels
    "knowledge_base": "WEBHOOK_KNOWLEDGE_BASE",
    "brief_room": "WEBHOOK_BRIEF_ROOM",
    "approvals": "WEBHOOK_APPROVALS",
    "action_plans": "WEBHOOK_ACTION_PLANS",
    "brainstorm": "WEBHOOK_BRAINSTORM",
    
    # Global Fallback
    "joy": "WEBHOOK_MISSION_CONTROL",
    "mission_control": "WEBHOOK_MISSION_CONTROL"
}

# --- FALLBACK: Channel IDs (If Webhooks are missing) ---
# Used for console logging "intent" if webhook fails
CHANNEL_ID_MAP = {
    "scout": "1474314240264507413",
    "analyst": "1474314325694087199",
    "broker": "1474314506858532936",
    "quill": "1474314626182418432",
    "overseer": "1474314408556626043",
    "echo": "1474314704427028560",
    "spark": "1474313962056319049",
    "weaver": "1474314836564246530",
    "alfred": "1474314917606854656",
    "cipher": "1474324481005846601",
    "archivist": "1474314996069695488",
    "brainstorm": "1474314056512049164",
    "action_plans": "1474314146798637107",
    "brief_room": "1474313186541965322",
    "approvals": "1474313860314959932",
    "knowledge_base": "1474314996069695488", # Same as archivist
    "joy": "1474314146798637107"
}

def post(agent_name, msg_type, message):
    """
    agent_name: 'scout', 'quill', etc.
    msg_type: 'START', 'PROGRESS', 'DONE', 'ERROR', 'INFO'
    message: Human readable text
    """
    agent_key = agent_name.lower()
    
    # 1. Resolve Webhook URL
    env_var_name = WEBHOOK_ENV_MAP.get(agent_key)
    webhook_url = os.getenv(env_var_name) if env_var_name else None
    
    # Icons/Colors
    icon = ""
    color = 0x3498db # Default Blue
    if msg_type == "START": 
        icon = "[START]"
        color = 0x3498db # Blue
    elif msg_type == "PROGRESS": 
        icon = "[WORKING]"
        color = 0xf1c40f # Yellow
    elif msg_type == "DONE": 
        icon = "[DONE]"
        color = 0x2ecc71 # Green
    elif msg_type == "ERROR": 
        icon = "[ERROR]"
        color = 0xe74c3c # Red
    elif msg_type == "INFO":
        icon = "[INFO]"
        color = 0x95a5a6 # Grey

    # Format Message
    title = f"[{agent_name.upper()}] {msg_type}"
    desc = f"{icon} {message}"

    # 2. Send via Webhook (Priority)
    if webhook_url and webhook_url.startswith("http"):
        try:
            payload = {
                "username": f"{agent_name.capitalize()} (Bot)",
                # "avatar_url": "...", # Optional: Add agent avatars later
                "embeds": [{
                    "title": title,
                    "description": message, # Use raw message in desc, icon in title? Or vice versa
                    "color": color,
                    "footer": {"text": f"Mission Control • {msg_type}"},
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }
            # Simple content fallback if embeds fail or for simple logs
            # payload = {"content": f"**{title}**\n{desc}"} 
            
            res = requests.post(webhook_url, json=payload, timeout=5)
            if res.status_code in [200, 204]:
                print(f"[DISCORD] Sent to {agent_key} via Webhook.")
                return
            else:
                print(f"[DISCORD] Webhook Failed ({res.status_code}): {res.text}")
        except Exception as e:
            print(f"[DISCORD] Webhook Error: {e}")

    # 3. Fallback: Log Intent (The old way)
    # If webhook missing or failed, print the tag for the human operator/supervisor
    channel_id = CHANNEL_ID_MAP.get(agent_key, "UNKNOWN")
    full_msg = f"**[{agent_name.upper()}]** {icon} {message}"
    
    # try:
    #     sys.stdout.reconfigure(encoding='utf-8')
    # except:
    #     pass
    print(f"DISCORD_MSG::{channel_id}::{full_msg}")
    
    # Log to file
    try:
        with open("workspace/discord_stream.log", "a", encoding="utf-8") as f:
            f.write(f"{json.dumps({'channel': channel_id, 'msg': full_msg})}\n")
    except:
        pass

def request_approval(task, details):
    """
    Special function for Joy to ask for approval.
    """
    post("approvals", "INFO", f"**[APPROVAL REQUEST]** 🛑\n**Task:** {task}\n**Details:** {details}\n*Reply 'Approve' to proceed.*")

from datetime import datetime

if __name__ == "__main__":
    if len(sys.argv) > 3:
        post(sys.argv[1], sys.argv[2], sys.argv[3])
