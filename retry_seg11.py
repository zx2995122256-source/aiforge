import requests
BASE = "http://localhost:7862"
r = requests.post(f"{BASE}/api/auth/login", json={"email": "test@test.com", "password": "test123"})
token = r.json().get("token")
headers = {"Authorization": f"Bearer {token}"}
r = requests.post(f"{BASE}/api/project/27/retry/4/11", headers=headers, timeout=120)
print(f"Retry seg11: {r.status_code} {r.text[:200]}")
