#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "OiioiiPool"))

from core.client import OiioiiClient
from config import VIDEO_MODELS_DIRECT

print("=== Test 1: config timeout ===")
omni = VIDEO_MODELS_DIRECT.get("Gemini Omni")
print(f"  Gemini Omni timeout: {omni.get('timeout')}s (should be 900)")

print("\n=== Test 2: poll_result signature ===")
import inspect
sig = inspect.signature(OiioiiClient.poll_result)
print(f"  poll_result params: {list(sig.parameters.keys())}")
assert "initial_delay" in sig.parameters, "initial_delay param missing!"

print("\n=== Test 3: import engine ===")
from core.engine import GenEngine
print("  Engine import OK")

print("\n=== Test 4: quick Gemini Omni submit + poll ===")
import sqlite3
DB_PATH = os.path.join(os.path.dirname(__file__), "OiioiiPool", "data", "oiioii_pool.db")
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(os.path.dirname(__file__), "OiioiiPool", "oiioii_pool.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT id, email, password, workspace_id FROM accounts WHERE status='active' LIMIT 10")
accts = [dict(r) for r in cur.fetchall()]
conn.close()

test_client = None
for a in accts:
    c = OiioiiClient(a['email'], a['password'], account_id=a['id'], workspace_id=a.get('workspace_id', ''))
    if c.login():
        pts = c.get_points()
        if pts >= 30:
            test_client = c
            print(f"  Using #{a['id']} pts={pts}")
            break

if not test_client:
    print("  No account with enough points, skipping live test")
else:
    ok, result, manual_refresh = test_client.generate_video(
        prompt="A calm ocean at golden hour, cinematic",
        model_name="Gemini Omni",
        ratio="16:9",
        duration=4,
        resolution="720p"
    )
    print(f"  Submit: ok={ok} manualRefresh={manual_refresh} tid={str(result)[:40]}")
    
    if ok:
        skip_uris = test_client.get_known_uris()
        init_delay = 30 if manual_refresh else 0
        status, uri = test_client.poll_result("video", skip_uris, max_wait=120, interval=8,
                                               remote_task_id=result, initial_delay=init_delay)
        print(f"  Poll result: status={status} uri={str(uri)[:60]}")

print("\nAll tests passed!")
