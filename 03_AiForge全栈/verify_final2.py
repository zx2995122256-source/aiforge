import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()

css_match = re.findall(r'href="([^"]+\.css)"', html)
if css_match:
    css = urllib.request.urlopen(f"http://localhost:7862{css_match[0]}").read().decode()
    
    bad_values = ["#ffffffc7", "#ffffff14", "#ffffff26"]
    print(f"CSS: {len(css)} bytes")
    
    all_gone = True
    for v in bad_values:
        if v in css:
            print(f"  ❌ STILL PRESENT: {v}")
            all_gone = False
    if all_gone:
        print("  ✅ All !important override colors REMOVED")
    
    print(f"  Total !important: {css.count('!important')}")
    
    # Verify the CSS vars are correct
    for var in ["--text-primary", "--text-secondary", "--text-muted"]:
        idx = css.find(var)
        if idx >= 0:
            val_start = css.find(":", idx) + 1
            val_end = css.find(";", val_start)
            val = css[val_start:val_end].strip()
            print(f"  {var} = {val}")

    # Check Project JS for _alive
    js_match = re.findall(r'src="([^"]+Project-[^"]+\.js)"', html)
    if js_match:
        js = urllib.request.urlopen(f"http://localhost:7862{js_match[0]}").read().decode(errors="replace")
        for c in ["_alive", "onBeforeRouteLeave", "#181826", "#3a3a52"]:
            found = c in js
            print(f"  {'✅' if found else '❌'} {c} in Project JS")

import json
req = urllib.request.Request("http://localhost:7862/api/auth/login",
    data=json.dumps({"email":"sci_test@aiforge.ai","password":"sci2025pw"}).encode(),
    headers={"Content-Type":"application/json"})
rr = urllib.request.urlopen(req, timeout=10)
print(f"\n✅ Server OK: {json.loads(rr.read())['user']['points']} pts")

print("Done")