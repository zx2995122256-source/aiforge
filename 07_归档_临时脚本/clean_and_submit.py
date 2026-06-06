import requests, time, sqlite3

# Step 1: Clear ALL old stuck tasks from OiioiiPool
conn = sqlite3.connect(r"C:\Users\Administrator\Documents\OiioiiPool\data\oiioii_pool.db")
old = conn.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('processing','running')").fetchone()[0]
print(f"Old processing tasks: {old}")
conn.execute("DELETE FROM tasks WHERE status IN ('processing','running')")
conn.execute("DELETE FROM tasks WHERE status='pending'")
conn.commit()
print("Cleaned all stuck tasks")

# Check account points
rows = conn.execute("SELECT email, points FROM accounts WHERE status='active' ORDER BY points DESC LIMIT 5").fetchall()
print(f"\nTop 5 active accounts:")
for r in rows:
    print(f"  {r[0][:15]}...  {r[1]} pts")
conn.close()

# Step 2: Submit a SIMPLE video (no refs at all) directly to OiioiiPool
print("\n=== Submitting simple video ===")
body = {
    "prompt": "a cute cat walking",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "resolution": "720p",
    "duration": 5
}
r = requests.post("http://localhost:7861/api/generate_video", json=body, timeout=30)
print(f"Submit: {r.status_code}")
resp = r.json()
task_id = resp.get("task_id", resp.get("task_db_id", "?"))
print(f"Task ID: {task_id}")

# Poll
for i in range(6):
    time.sleep(10)
    r = requests.get(f"http://localhost:7861/api/task/{task_id}", timeout=10)
    t = r.json()
    s = t.get("status", "?")
    e = t.get("error", "")
    ruri = t.get("result_uri", "")[:30]
    print(f"  [{i*10+10}s] {s:12} error={e[:30]} result={ruri}")
    if s == "completed" or s == "failed":
        break