import requests, time

# Submit a simple task directly to OiioiiPool
body = {
    "prompt": "a cute cat walking",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "resolution": "720p",
    "duration": 5
}
print("Submitting to OiioiiPool...")
r = requests.post("http://localhost:7861/api/generate_video", json=body, timeout=30)
print(f"Submit: {r.status_code}")
if r.status_code == 200:
    task_id = r.json().get("task_id", "?")
    print(f"Task ID: {task_id}")
    
    # Check after 5 seconds
    time.sleep(5)
    r2 = requests.get(f"http://localhost:7861/api/task/{task_id}", timeout=10)
    t = r2.json()
    print(f"After 5s: status={t.get('status','?')}")
    if t.get("error"):
        print(f"  Error: {t['error']}")
else:
    print(f"Error: {r.text[:200]}")