import requests, json, time

# Start continuous registration targeting 100 more accounts
# Current: 155, target: 255
r = requests.post("http://localhost:7861/api/pool/continuous_reg", json={"target": 255}, timeout=30)
print(f"Continuous reg started: {r.status_code}")
print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:300])

# Monitor progress
for i in range(10):
    time.sleep(30)
    r = requests.get("http://localhost:7861/api/pool/status", timeout=15)
    data = r.json()
    total = data.get("total_accounts", "?")
    active = data.get("active_accounts", "?")
    running = data.get("continuous_reg_running", False)
    print(f"  [{(i+1)*30}s] Total: {total} | Active: {active} | Reg running: {running}")
    if not running:
        print("Registration stopped")
        break
