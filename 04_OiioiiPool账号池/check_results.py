import urllib.request, json, time

base = "http://localhost:7861"

# Check tasks 1572-1575 (Nano Pro, Nano 2, Niji7, GPT-Image2)
for tid in [1572, 1573, 1574, 1575]:
    try:
        resp = urllib.request.urlopen(base + "/api/task/" + str(tid))
        data = json.loads(resp.read().decode())
        status = data.get("status", "")
        model = data.get("model_name", "")
        result = data.get("result_uri", "") or data.get("result_url", "") or ""
        err = data.get("error_message", "") or ""
        print(f"#{tid} {model}: status={status} result={result[:80] if result else 'none'} err={err[:80]}")
    except Exception as e:
        print(f"#{tid}: error - {e}")

# Also check recent tasks from DB
import sqlite3
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id,task_type,model_name,status,result_uri,error_message FROM tasks ORDER BY id DESC LIMIT 10").fetchall()
print("\n--- Recent 10 tasks ---")
for r in rows:
    d = dict(r)
    print(f"#{d['id']} {d['model_name']}: {d['status']} uri={str(d.get('result_uri',''))[:60]} err={str(d.get('error_message',''))[:60]}")
conn.close()
