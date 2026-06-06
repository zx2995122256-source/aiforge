import requests, json, time, sys

BASE = "http://localhost:7862"

# Try to register a new user
r = requests.post(f"{BASE}/api/auth/register", json={
    "email": "abyss@aiforge.local",
    "password": "abyss123"
})
print("Register:", r.status_code, r.text[:200])

# Login
r = requests.post(f"{BASE}/api/auth/login", json={
    "email": "abyss@aiforge.local",
    "password": "abyss123"
})
print("Login:", r.status_code)
data = r.json()
token = data.get("access_token") or data.get("token")
print("Token:", token[:50] if token else "None")

if token:
    # Create project
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/project/create", headers=headers, json={
        "name": "深渊之航 Ep1 - 2min"
    })
    print("Create project:", r.status_code, r.text[:300])
    proj = r.json()
    project_id = proj.get("id")
    print(f"Project ID: {project_id}")
