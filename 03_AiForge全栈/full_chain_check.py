import urllib.request, re, os, json

# === 1. Check backend config - what frontend dir is it REALLY using? ===
# Read main.py to get the default
with open("/home/ubuntu/aiforge/backend/main.py") as f:
    main_py = f.read()

frontend_line = [l for l in main_py.split("\n") if "FRONTEND_DIR" in l or "frontend" in l.lower()]
for l in frontend_line:
    print(f"Backend config: {l.strip()}")

# Check env var
print(f"ENV AIFORGE_FRONTEND_DIR: {os.environ.get('AIFORGE_FRONTEND_DIR', 'NOT SET')}")

# === 2. Check what the backend ACTUALLY serves (not nginx, directly to 7862) ===
print("\n--- Backend direct (port 7862) ---")
r = urllib.request.urlopen("http://localhost:7862/")
html_b = r.read().decode()
css_b = re.findall(r'href="([^"]+\.css)"', html_b)
js_b = re.findall(r'src="([^"]+\.js)"', html_b)
print(f"HTML: {len(html_b)} bytes")
print(f"CSS: {css_b[0] if css_b else 'NONE'}")
proj = [j for j in js_b if 'Project' in j]
print(f"Project JS directly: {proj[0] if proj else 'NOT IN HTML (lazy)'}")

# === 3. Check what Nginx serves ===
print("\n--- Nginx (port 80) ---")
r = urllib.request.urlopen("http://localhost/")
html_n = r.read().decode()
css_n = re.findall(r'href="([^"]+\.css)"', html_n)
print(f"HTML: {len(html_n)} bytes")
print(f"CSS: {css_n[0] if css_n else 'NONE'}")

# Compare
if html_b == html_n:
    print("✅ Backend and Nginx serve IDENTICAL HTML")
else:
    print("❌ DIFFERENT HTML!")
    print(f"  Backend: {len(html_b)}b, Nginx: {len(html_n)}b")
    # Show differences
    for i, (a, b) in enumerate(zip(html_b.split("\n"), html_n.split("\n"))):
        if a != b:
            print(f"  Diff line {i}:")
            print(f"    Backend: {a[:100]}")
            print(f"    Nginx:   {b[:100]}")

# === 4. Check that the dist directory on disk matches what Nginx serves ===
dist_idx = "/home/ubuntu/aiforge/dist/index.html"
if os.path.exists(dist_idx):
    with open(dist_idx) as f:
        disk_html = f.read()
    if disk_html.strip() == html_n.strip():
        print("\n✅ Dist HTML on disk == Nginx serves (perfect match)")
    else:
        print(f"\n❌ Dist HTML != Nginx serves")
        print(f"  Disk: {len(disk_html)}b, Nginx: {len(html_n)}b")

# === 5. Check Project JS literally ===  
dist_assets = "/home/ubuntu/aiforge/dist/assets"
proj_files = sorted([f for f in os.listdir(dist_assets) if f.startswith("Project-") and f.endswith(".js")])
if proj_files:
    latest = os.path.join(dist_assets, proj_files[-1])
    with open(latest, "rb") as fh:
        js = fh.read().decode(errors="replace")
    print(f"\nDist Project JS: {proj_files[-1]} ({len(js)} bytes)")
    for c in ["style=", "background:#1a1a2e", "chat-input-wrap", "watch", "_alive"]:
        found = c in js
        print(f"  {'✅' if found else '❌'} {c}")

# === 6. Compare the dist JS with what the backend serves ===
# (Project is lazy-loaded, need to hit the route)
print("\n--- Serving test: requesting Project JS from backend ---")
req = urllib.request.urlopen(f"http://localhost:7862/assets/{proj_files[-1]}")
served_js = req.read().decode(errors="replace")
print(f"Backend serves Project JS: {len(served_js)} bytes")
print(f"Match with disk: {served_js == js}")

# Also from Nginx
req2 = urllib.request.urlopen(f"http://localhost/assets/{proj_files[-1]}")
nginx_js = req2.read().decode(errors="replace")
print(f"Nginx serves Project JS: {len(nginx_js)} bytes")
print(f"Match with disk: {nginx_js == js}")

print("\nDONE")