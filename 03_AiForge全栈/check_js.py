import urllib.request, re

r = urllib.request.urlopen("http://localhost/")
html = r.read().decode()
css_match = re.findall(r'href="([^"]+\.css)"', html)
js_match = re.findall(r'src="([^"]+\.js)"', html)

print(f"CSS: {css_match[0] if css_match else 'NONE'}")
proj_js = [j for j in js_match if "Project" in j]
print(f"Project JS: {proj_js[0] if proj_js else 'NONE'}")

if proj_js:
    js = urllib.request.urlopen(f"http://localhost{proj_js[0]}").read().decode(errors="replace")
    for c in ["onBeforeRouteLeave", "_alive", "#181826", "#3a3a52", "focus-within"]:
        found = c in js
        print(f"  {'✅' if found else '❌'} {c}")
    print(f"Project JS size: {len(js)} bytes")

print("Done")