import urllib.request, re

# Check via Nginx (port 80)
r = urllib.request.urlopen("http://localhost/")
html = r.read().decode()
css_match = re.findall(r'href="([^"]+\.css)"', html)
print(f"Nginx serves: {css_match[0] if css_match else 'NO CSS'}")

if css_match:
    css_url = f"http://localhost{css_match[0]}"
    css = urllib.request.urlopen(css_url).read().decode()
    print(f"CSS size: {len(css)} bytes")
    for v in ["#eeeeef", "#b8b8c0", "#909098", "#181826", "#3a3a52"]:
        count = css.count(v)
        print(f"  {v}: {count}x")
    print(f"\nCache headers:")
print("URL: http://localhost/")
print(f"CSS URL: {css_url if css_match else 'N/A'}")

import json
req = urllib.request.Request("http://localhost/api/auth/login",
    data=json.dumps({"email":"sci_test@aiforge.ai","password":"sci2025pw"}).encode(),
    headers={"Content-Type":"application/json"})
rr = urllib.request.urlopen(req, timeout=10)
print(f"\nAPI via Nginx: ✅ {json.loads(rr.read())['user']['points']} pts")

print("\nDone")