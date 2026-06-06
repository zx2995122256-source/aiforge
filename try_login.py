import requests, json

BASE = "http://localhost:7862"

# Try login with existing accounts
accounts = [
    ("xiaye@aiforge.com", "xiaye123"),
    ("xiaye@aiforge.com", "123456"),
    ("xiaye@aiforge.com", "xiaye"),
    ("test@test.com", "test123"),
    ("test@test.com", "123456"),
]

for email, pwd in accounts:
    r = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": pwd})
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token") or data.get("token")
        print(f"SUCCESS: {email} / {pwd}")
        print(f"Token: {token[:50]}")
        break
    else:
        print(f"FAIL: {email} / {pwd} -> {r.status_code}")
