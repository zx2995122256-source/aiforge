import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
print(f"HTTP: 200 OK")

css_matches = re.findall(r'href="([^"]+\.css)"', html)
if css_matches:
    main_css = css_matches[0]
    r2 = urllib.request.urlopen(f"http://localhost:7862{main_css}")
    css = r2.read().decode()
    
    print(f"CSS: {main_css} ({len(css)} bytes)")
    
    checks = [
        ("--bg-card: rgba(22,22,36,0.7)", "Brighter bg-card (new)"),
        ("--text-primary: #eeeeef", "Brighter text-primary (new)"),
        ("--text-secondary: #b8b8c0", "Brighter text-secondary (new)"),
        ("--text-muted: #909098", "Brighter text-muted (new)"),
        ("--border-color: rgba", "border-color exists"),
        ("--accent: #7c8ab5", "accent color"),
        ("btn-primary {", "btn-primary class"),
        ("btn-secondary {", "btn-secondary class"),
        ("shimmer", "shimmer skeleton"),
    ]
    for keyword, label in checks:
        found = keyword in css
        marker = "✅" if found else "❌"
        print(f"  {marker} {label}")

# Check login
import json
r = urllib.request.Request("http://localhost:7862/api/auth/login",
    data=json.dumps({"email":"sci_test@aiforge.ai","password":"sci2025pw"}).encode(),
    headers={"Content-Type":"application/json"})
try:
    rr = urllib.request.urlopen(r, timeout=10)
    print(f"\n✅ Login OK: {json.loads(rr.read())['user']['points']} pts")
except Exception as e:
    print(f"\n❌ Login fail: {e}")

print("\n✅ Verify complete")