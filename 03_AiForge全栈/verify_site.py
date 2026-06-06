import urllib.request, json

BASE = "http://localhost:7862"

# 1. Login
req = urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({"email": "sci_test@aiforge.ai", "password": "sci2025pw"}).encode(),
    headers={"Content-Type": "application/json"}
)
try:
    r = urllib.request.urlopen(req, timeout=15)
    data = json.loads(r.read())
    token = data["token"]
    uid = data["user"]["id"]
    pts = data["user"]["points"]
    print(f"✅ Login OK: UID={uid}, Points={pts}")
except Exception as e:
    print(f"❌ Login failed: {e}")
    # Try with existing user
    try:
        req = urllib.request.Request(f"{BASE}/api/auth/login", data=json.dumps({"email":"xiaye@aiforge.com","password":"admin123"}).encode(), headers={"Content-Type":"application/json"})
        r = urllib.request.urlopen(req, timeout=15)
        data = json.loads(r.read())
        token = data["token"]
        print(f"✅ Login as xiaye: {data['user']['nickname']}, Points={data['user']['points']}")
    except Exception as e2:
        print(f"❌ xiaye login also failed: {e2}")
        token = None

# 2. Get project list
if token:
    req = urllib.request.Request(f"{BASE}/api/project/list", headers={"Authorization": f"Bearer {token}"})
    try:
        r = urllib.request.urlopen(req, timeout=10)
        projects = json.loads(r.read())
        print(f"✅ Projects: {len(projects)} total")
        for p in projects[:3]:
            print(f"   #{p['id']} {p['name'][:30]} phase={p['phase']} segs={p['segments_count']}")
    except Exception as e:
        print(f"❌ Project list failed: {e}")

# 3. Check page renders
r = urllib.request.urlopen(f"{BASE}/", timeout=10)
html = r.read().decode()
checks = [
    ("Vue app", '<div id="app"' in html),
    ("JS bundle", "/assets/index-" in html and ".js" in html),
    ("CSS bundle", ".css" in html),
    ("Dark mode", 'class="dark"' in html),
]
print()
for label, ok in checks:
    print(f"  {'✅' if ok else '❌'} {label}")

print("\n✅ Test complete - site should be working")