#!/usr/bin/env python3
"""Step 1: Create project and submit script only."""
import requests, json, sys

BASE = "http://localhost:7862"

# Read assets and segments from main script
exec(open("create_abyss_road.py").read(), globals())

# Login
r = requests.post(f"{BASE}/api/auth/login", json={"email": "test@test.com", "password": "test123"})
if r.status_code != 200:
    print("Login failed:", r.status_code, r.text[:200])
    sys.exit(1)
token = r.json().get("access_token")
print("Login OK, token:", token[:30])

headers = {"Authorization": f"Bearer {token}"}

# Create project with script
script_json = {"segments": SEGMENTS, "assets": ASSETS}
r = requests.post(f"{BASE}/api/project/create", headers=headers, json={
    "name": "深渊之航 Ep1 - 2min",
    "script": json.dumps(script_json, ensure_ascii=False),
    "raw_script": "2min Cthulhu x Age of Sail: The Abyss Road Ep1. 12 segments x 10s.",
    "video_model": "Gemini Omni",
    "image_model": "GPT-Image2",
    "ratio": "9:16",
    "resolution": "720p",
    "duration": 10
})
print("Create project:", r.status_code)
proj = r.json()
pid = proj.get("id")
print(f"Project ID: {pid}, Segments: {proj.get('segments')}, Assets: {proj.get('assets')}")

# Phase 2: Generate assets
print("\n=== Phase 2: Generating Assets ===")
for i in range(len(ASSETS)):
    r = requests.post(f"{BASE}/api/project/{pid}/asset/{i}/generate", headers=headers)
    print(f"  Asset {i} ({ASSETS[i]['name']}): {r.status_code}")

print(f"\nProject {pid} created with assets generating. Run phase3+4 later.")
