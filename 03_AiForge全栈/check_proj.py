import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()

js_files = re.findall(r'src="([^"]+\.js)"', html)
print(f"JS files: {len(js_files)}")
for j in js_files:
    if "Project" in j:
        print(f"Project JS: {j}")
        js = urllib.request.urlopen(f"http://localhost:7862{j}").read().decode(errors="replace")
        for c in ["onBeforeRouteLeave", "_alive", "#181826", "#3a3a52"]:
            print(f"  {'✅' if c in js else '❌'} {c}")
        print(f"  Size: {len(js)} bytes")

print("Done")