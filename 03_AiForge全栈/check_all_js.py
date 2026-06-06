import urllib.request, re, json

r = urllib.request.urlopen("http://localhost/")
html = r.read().decode()
js_all = re.findall(r'src="([^"]+\.js)"', html)
proj_js = [j for j in js_all if "Project" in j]
print(f"JS files in HTML: {len(js_all)}")
print(f"Project JS: {proj_js}")

# Check ALL JS for the key changes
for j in js_all:
    try:
        js = urllib.request.urlopen(f"http://localhost{j}").read().decode(errors="replace")
        for c in ["onBeforeRouteLeave", "_alive"]:
            if c in js:
                print(f"✅ '{c}' FOUND in {j}")
    except:
        pass

# Check dist file directly for the Project chunk
import os
dist_dir = "/home/ubuntu/aiforge/dist/assets"
if os.path.exists(dist_dir):
    files = [f for f in os.listdir(dist_dir) if "Project" in f]
    print(f"\nProject files in dist: {files}")
    for f in files:
        fp = os.path.join(dist_dir, f)
        with open(fp, "rb") as fh:
            content = fh.read().decode(errors="replace")
        for c in ["onBeforeRouteLeave", "_alive", "#181826"]:
            if c in content:
                print(f"  ✅ '{c}' in {f}")

print("\nDone")