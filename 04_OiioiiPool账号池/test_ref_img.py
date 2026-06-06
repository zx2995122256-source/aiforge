import urllib.request, json, time

base = "http://localhost:7861"

# Use a known existing image as reference
# First, find a completed image task to use its result as ref
import sqlite3
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT result_uri FROM tasks WHERE task_type='image' AND status='completed' AND result_uri LIKE 'hogi%' ORDER BY id DESC LIMIT 1").fetchone()
ref_uri = row["result_uri"] if row else ""
conn.close()
print(f"Using ref image: {ref_uri}")

# Test each image model with reference image
models = ["GPT-Image2", "Nano Pro", "Nano 2", "Niji7", "Niji6", "Seedream 5.0", "Seedream 4.5", "Flux", "NovelAI", "Gpt 4o"]

for model in models:
    data = json.dumps({
        "prompt": "a cute cat wearing a hat",
        "model": model,
        "ratio": "1:1",
        "resolution": "1K",
        "reference_images": [ref_uri] if ref_uri else []
    }).encode()
    req = urllib.request.Request(base + "/api/generate_image", data=data, headers={"Content-Type":"application/json"})
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        print(f"{model}: submitted task_id={result.get('task_id')}")
    except Exception as e:
        err = e.read().decode() if hasattr(e,"read") else str(e)
        print(f"{model}: ERROR - {err[:120]}")

# Wait and check results
print("\nWaiting 30s for results...")
time.sleep(30)

import sqlite3
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, model_name, status, error_message FROM tasks ORDER BY id DESC LIMIT 12").fetchall()
print("\n--- Results ---")
for r in rows:
    d = dict(r)
    err = str(d.get("error_message",""))[:80]
    print(f"#{d['id']} {d['model_name']}: {d['status']} {('err='+err) if err else ''}")
conn.close()
