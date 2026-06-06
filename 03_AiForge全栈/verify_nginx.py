import urllib.request, re

r = urllib.request.urlopen("http://localhost/")
print(f"Status: {r.status}")
print(f"Cache-Control: {r.headers.get('Cache-Control','NONE')}")
print(f"Expires: {r.headers.get('Expires','NONE')}")

html = r.read().decode()
css_match = re.findall(r'href="([^"]+\.css)"', html)
print(f"\nCSS file: {css_match[0] if css_match else 'NONE'}")

if css_match:
    r2 = urllib.request.urlopen(f"http://localhost{css_match[0]}")
    css = r2.read().decode()
    print(f"Cache-Control for CSS: {r2.headers.get('Cache-Control','NONE')}")
    print(f"CSS size: {len(css)} bytes")
    
    checks = [
        ("#eeeeef", "bright primary"),
        ("#b8b8c0", "bright secondary"),
        ("#909098", "bright muted"),
        ("#181826", "agent bg"),
        ("#3a3a52", "agent border"),
        ("#w00", "will fail"),
    ]
    for val, label in checks:
        print(f"  {'✅' if val in css else '❌'} {label}")

    # Check Project JS
    js_match = re.findall(r'src="([^"]+Project-[^"]+\.js)"', html)
    if js_match:
        r3 = urllib.request.urlopen(f"http://localhost{js_match[0]}")
        js = r3.read().decode(errors="replace")
        for c in ["#181826", "#3a3a52", "onBeforeRouteLeave", "_alive", "bg-transparent"]:
            print(f"  {'✅' if c in js else '❌'} {c} in Project JS")

import json
req = urllib.request.Request("http://localhost/api/auth/login",
    data=json.dumps({"email":"sci_test@aiforge.ai","password":"sci2025pw"}).encode(),
    headers={"Content-Type":"application/json"})
rr = urllib.request.urlopen(req, timeout=10)
print(f"\nAPI: ✅ {json.loads(rr.read())['user']['points']} pts")

print("\nDone")