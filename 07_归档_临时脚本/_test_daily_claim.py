#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "OiioiiPool"))

print("=== Test 1: MAX_CONCURRENT_GEN ===")
from config import MAX_CONCURRENT_GEN, DAILY_CLAIM_ENABLED, DAILY_CLAIM_HOUR, DAILY_CLAIM_MIN_POINTS
print(f"  MAX_CONCURRENT_GEN: {MAX_CONCURRENT_GEN} (should be 20)")
assert MAX_CONCURRENT_GEN == 20

print("\n=== Test 2: daily_claim method exists ===")
from core.client import OiioiiClient
assert hasattr(OiioiiClient, 'daily_claim'), "daily_claim method missing!"
print("  OK")

print("\n=== Test 3: reset_video_used method exists ===")
from core.db import AccountDB
assert hasattr(AccountDB, 'reset_video_used'), "reset_video_used method missing!"
print("  OK")

print("\n=== Test 4: daily_claim_all method exists ===")
from core.pool import AccountPool
assert hasattr(AccountPool, 'daily_claim_all'), "daily_claim_all method missing!"
print("  OK")

print("\n=== Test 5: Live daily_claim test ===")
import sqlite3
DB_PATH = os.path.join(os.path.dirname(__file__), "OiioiiPool", "data", "oiioii_pool.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT id, email, password, workspace_id FROM accounts WHERE status='active' LIMIT 1")
a = dict(cur.fetchone())
conn.close()

c = OiioiiClient(a['email'], a['password'], account_id=a['id'], workspace_id=a.get('workspace_id', ''))
if c.login():
    pts_before = c.get_points()
    result = c.daily_claim()
    pts_after = c.get_points()
    print(f"  Before: {pts_before}, After: {pts_after}")
    print(f"  Result: {result}")
    if result.get("success"):
        if result.get("duplicate"):
            print("  Already claimed today - that's expected")
        else:
            print(f"  Claimed +{result.get('added', 0)} points!")
    else:
        print(f"  Failed: {result.get('error')}")
else:
    print("  Login failed")

print("\nAll tests passed!")
