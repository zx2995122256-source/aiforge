import requests, json
BASE = "http://localhost:7862"
r = requests.post(f"{BASE}/api/auth/login", json={"email": "test@test.com", "password": "test123"})
print("Status:", r.status_code)
print("Response:", r.text[:500])
if r.status_code == 200:
    data = r.json()
    print("Keys:", list(data.keys()))
    token = data.get("access_token") or data.get("token") or data.get("access_token")
    print("Token:", token[:50] if token else "NONE")
