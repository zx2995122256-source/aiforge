import requests, json, sys, time

url = "http://localhost:7861/api/generate_video"
body = {
    "prompt": "A beautiful sunset over the ocean with golden light reflecting on calm waves, cinematic",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "resolution": "4K",
    "duration": 6
}

print(f"Submitting 4K Gemini Omni video...", flush=True)
try:
    r = requests.post(url, json=body, timeout=60)
    print(f"Status: {r.status_code}", flush=True)
    print(f"Response: {r.text[:500]}", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
    sys.exit(1)

if r.status_code == 200:
    data = r.json()
    task_id = data.get("task_id") or data.get("id")
    print(f"Task ID: {task_id}", flush=True)
    if task_id:
        for i in range(60):
            time.sleep(5)
            try:
                pr = requests.get(f"http://localhost:7861/api/task/{task_id}", timeout=30)
                pdata = pr.json()
                status = pdata.get("status", "unknown")
                print(f"  [{(i+1)*5}s] {status}", flush=True)
                if status in ("completed", "failed", "timeout"):
                    print(f"Result: {json.dumps(pdata, indent=2, ensure_ascii=False)[:1500]}", flush=True)
                    break
            except Exception as e:
                print(f"  [{(i+1)*5}s] poll error: {e}", flush=True)
