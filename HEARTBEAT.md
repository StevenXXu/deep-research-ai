# HEARTBEAT.md
# (keep empty to skip heartbeat API calls)

# Notes
# - Steven LinkedIn Daily Flywheel: always use isolated browser (profile="openclaw"); do NOT rely on Chrome Relay.

# System Event Handlers
# When receiving these system events, automatically run the corresponding action:

RUN_SCAN_HK_SIGNALS: |
  When receiving "RUN_SCAN_HK_SIGNALS" system event:
  1. Execute: cd C:\Users\StevenDesk\clawd\tradingbot && python scan_hk_signals.py
  2. The script will:
     - Check if within HK trading hours (HKT 9:30-12:00, 13:00-16:00)
     - Scan 4 HK stocks: HK.0700, HK.9988, HK.3690, HK.1810
     - Send signals to tradinbot channel (1469995528358985808)
     - Avoid duplicate signals (7-day window)
  3. Do NOT ask for confirmation - just execute silently
  4. Output a brief summary: "Scanned HK stocks: X signals sent, Y skipped"

RUN_SCAN_HK_OPTIONS: |
  When receiving "RUN_SCAN_HK_OPTIONS" system event:
  1. Execute: cd C:\Users\StevenDesk\clawd\tradingbot && python scan_hk_options.py
  2. The script will:
     - Check if within HK trading hours (HKT 9:30-12:00, 13:00-16:00)
     - Scan option chains for 4 HK stocks: HK.0700, HK.9988, HK.3690, HK.1810
     - Analyze ATM options opportunities (default DTE: 30 days)
     - Send signals to tradinbot channel (1469995528358985808)
     - Avoid duplicate signals (7-day window)
  3. Do NOT ask for confirmation - just execute silently
  4. Output a brief summary: "Scanned HK options: X signals sent, Y skipped"
