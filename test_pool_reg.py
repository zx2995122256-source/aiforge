import requests, json, time

# Try oiioii pool's built-in register endpoint
r = requests.post("http://localhost:7861/api/pool/register", json={"count": 1}, timeout=120)
print(f"Pool register: {r.status_code}")
print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:500])

# Also try continuous_reg
r2 = requests.post("http://localhost:7861/api/pool/continuous_reg", json={"target": 100}, timeout=30)
print(f"\nContinuous reg: {r2.status_code}")
print(json.dumps(r2.json(), indent=2, ensure_ascii=False)[:500])
