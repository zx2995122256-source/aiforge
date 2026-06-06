import urllib.request, re, os

# Check Nginx (user-facing)
r = urllib.request.urlopen("http://localhost/")
html = r.read().decode()
print(f"Nginx Cache: {r.headers.get('Cache-Control')}")
js = re.findall(r'src="([^"]+\.js)"', html)
proj_js = [j for j in js if "Project" in j and "chunk" not in j.lower() and "vendor" not in j.lower()]

# Project is lazy loaded, check dist file directly
dist = "/home/ubuntu/aiforge/dist/assets"
proj_files = sorted([f for f in os.listdir(dist) if f.startswith("Project-") and f.endswith(".js")])
print(f"\nProject JS in dist: {proj_files[-1] if proj_files else 'NONE'}")

if proj_files:
    with open(os.path.join(dist, proj_files[-1]), "rb") as fh:
        js = fh.read().decode(errors="replace")
    
    checks = [
        ("#1a1a2e", "Agent input bg"),
        ("#4a4a66", "Agent input border"),
        ("#7c3aed", "Send button / focus"),
        ("chat-input-wrap", "Scoped class"),
        ("watch", "Route watch"),
        ("_alive", "Alive flag"),
    ]
    for val, label in checks:
        found = val in js
        print(f"  {'✅' if found else '❌'} {label} ({val})")

print("\nDone")