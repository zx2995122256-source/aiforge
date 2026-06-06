import requests, json
BASE = "http://localhost:7862"
r = requests.post(f"{BASE}/api/auth/login", json={"email": "test@test.com", "password": "test123"})
token = r.json().get("token")
headers = {"Authorization": f"Bearer {token}"}

r = requests.get(f"{BASE}/api/project/27", headers=headers)
proj = r.json()

# Assets
assets = proj.get("assets", [])
print(f"Assets: {len(assets)}")
for i, a in enumerate(assets):
    url = a.get("result_url", "")
    err = a.get("error", "")
    status = "DONE" if url else ("ERROR: " + err[:50] if err else "pending")
    print(f"  {i}: {a.get('name','?')} -> {status}")

# Segments
segs = proj.get("segments", [])
print(f"\nSegments: {len(segs)}")
for i, s in enumerate(segs):
    sb = s.get("storyboard_url", "")
    vid = s.get("video_url", "")
    verr = s.get("video_error", "")
    status = ""
    if vid:
        status = "VIDEO DONE"
    elif verr:
        status = f"VIDEO ERROR: {verr[:60]}"
    elif sb:
        status = "STORYBOARD DONE"
    else:
        status = "pending"
    print(f"  {i}: {s.get('title','?')} -> {status}")
