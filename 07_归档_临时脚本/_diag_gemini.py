#!/usr/bin/env python3
import os, sys, glob
sys.path.insert(0, "/opt/OiioiiPool")

log_dir = "/opt/OiioiiPool/logs"
log_files = sorted(glob.glob(os.path.join(log_dir, "*.log")), key=os.path.getmtime, reverse=True)

if not log_files:
    print("No log files found")
    sys.exit(0)

print(f"Latest log: {log_files[0]}")
print(f"Size: {os.path.getsize(log_files[0])} bytes")
print("=" * 80)

with open(log_files[0], "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

keywords = ["gemini", "omni", "manualRefresh", "FOUND", "TIMEOUT", "FAILED", "submit", "poll #", "video_generate"]
matching = []
for i, line in enumerate(lines):
    low = line.lower()
    if any(k.lower() in low for k in keywords):
        matching.append(f"L{i+1}: {line.rstrip()}")

print(f"Matching lines: {len(matching)}")
print("=" * 80)
for m in matching[-80:]:
    print(m)

print("\n\n=== Recent task results from DB ===")
try:
    import sqlite3
    db_path = "/opt/OiioiiPool/data/oiioii_pool.db"
    if not os.path.exists(db_path):
        db_path = "/opt/OiioiiPool/oiioii_pool.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, task_type, model_name, status, error_message, points_cost, created_at FROM tasks ORDER BY id DESC LIMIT 30")
    rows = cur.fetchall()
    for r in rows:
        print(f"Task#{r['id']}: type={r['task_type']} model={r['model_name']} status={r['status']} cost={r['points_cost']} err={str(r['error_message'] or '')[:60]}")
    conn.close()
except Exception as e:
    print(f"DB error: {e}")
