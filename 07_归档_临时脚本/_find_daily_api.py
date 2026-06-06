#!/usr/bin/env python3
import requests, re

r = requests.get("https://www.oiioii.ai/assets/index-QTxXdi-K.js", timeout=30,
    headers={"User-Agent": "Mozilla/5.0 Chrome/136.0.0.0"})
js = r.text

keywords = ["check_in", "checkin", "check-in", "daily_reward", "daily_reward", "claim", "sign_in",
            "receive_reward", "daily_points", "daily_credit", "free_points", "bonus",
            "签到", "领取", "claimReward", "claimDaily", "dailyClaim"]

for kw in keywords:
    pos = js.find(kw)
    if pos != -1:
        start = max(0, pos - 150)
        end = min(len(js), pos + 300)
        print(f"\n=== {kw} at {pos} ===")
        print(js[start:end])

print("\n\n=== Searching for points/credit related API endpoints ===")
for pattern in ["/points/", "/credit/", "/reward/", "/bonus/", "/daily/"]:
    positions = [m.start() for m in re.finditer(re.escape(pattern), js)]
    for pos in positions[:3]:
        start = max(0, pos - 100)
        end = min(len(js), pos + 200)
        print(f"\n--- {pattern} at {pos} ---")
        print(js[start:end])
