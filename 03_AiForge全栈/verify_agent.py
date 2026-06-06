import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()

css_match = re.findall(r'href="([^"]+\.css)"', html)
if css_match:
    css = urllib.request.urlopen(f"http://localhost:7862{css_match[0]}").read().decode()
    print(f"CSS: {len(css)} bytes")
    for c in ["rgba(255,255,255,0.78)", "rgba(255,255,255,0.08)", "!important"]:
        print(f"  {'✅' if c in css else '❌'} {c}")

js_match = re.findall(r'src="([^"]+Project-[^"]+\.js)"', html)
if js_match:
    js = urllib.request.urlopen(f"http://localhost:7862{js_match[0]}").read().decode(errors="replace")
    checks = ["bg-[#181826]", "border-[#3a3a52]", "focus-within", "onBeforeRouteLeave"]
    for c in checks:
        found = c in js
        print(f"  {'✅' if found else '❌'} {c} in Project JS")

print("Done")