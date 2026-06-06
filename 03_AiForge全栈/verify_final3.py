import urllib.request, re

r = urllib.request.urlopen("http://localhost/")
html = r.read().decode()
print(f"Cache-Control: {r.headers.get('Cache-Control','NONE')}")

css_match = re.findall(r'href="([^"]+\.css)"', html)
print(f"CSS: {css_match[0] if css_match else 'NONE'}")

js_match = re.findall(r'src="([^"]+Project-[^"]+\.js)"', html)
if js_match:
    js = urllib.request.urlopen(f"http://localhost{js_match[0]}").read().decode(errors="replace")
    checks = ["onBeforeRouteLeave", "_alive", "bg-\\[#181826\\]", "\\[#3a3a52\\]", "focus-within"]
    print(f"\nProject JS: {js_match[0]} ({len(js)} bytes)")
    for c in checks:
        raw = c.replace("\\[", "[").replace("\\]", "]")
        found = raw in js
        print(f"  {'✅' if found else '❌'} {raw}")

print("\nDone")