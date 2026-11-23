#!/usr/bin/env python3
"""Send report.md to Telegram, or skip gracefully when secrets are empty.

Required env (GitHub Secrets, not in code): TG_BOT_TOKEN, TG_CHAT_ID.
v1 has no Telegram target yet, so this step is a no-op until the user
confirms the target group and creates the bot via BotFather.
"""
import os
import sys
import urllib.request
import urllib.error
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    token = os.environ.get("TG_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TG_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("Telegram secrets not set, skipping Telegram report.")
        return 0
    text = (ROOT / "report.md").read_text(encoding="utf-8")
    if len(text) > 4000:
        text = text[:4000]
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(resp.status, resp.read().decode("utf-8", "ignore")[:500])
    except urllib.error.HTTPError as e:
        print(f"Telegram send failed: {e.code} {e.read().decode('utf-8', 'ignore')[:500]}")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
