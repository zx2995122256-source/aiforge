import urllib.request, re

# Check what HTML serves
r = urllib.request.urlopen("http://localhost/")
html = r.read().decode()

js_all = re.findall(r'src="([^"]+\.js)"', html)
print(f"JS via Nginx: {len(js_all)}")

# Check the main JS index file for onBeforeRouteLeave
for j in js_all:
    if "index-" in j and j.count("/") <= 1:
        js = urllib.request.urlopen(f"http://localhost{j}").read().decode(errors="replace")
        print(f"Main JS: {j.split('/')[-1]} ({len(js)} bytes)")
        for c in ["onBeforeRouteLeave", "_alive"]:
            if c in js:
                print(f"  ✅ {c} found")
                break
        else:
            # Try to find similar minified patterns
            if "beforeRouteLeave" in js:
                print(f"  ⚠️  beforeRouteLeave (without 'on') found")
            else:
                print(f"  ❌ neither found")

# Check Project JS file directly on disk
import os
dist = "/home/ubuntu/aiforge/dist/assets"
proj_files = sorted([f for f in os.listdir(dist) if f.startswith("Project-") and f.endswith(".js")])
print(f"\nProject JS files: {len(proj_files)}")
if proj_files:
    latest = os.path.join(dist, proj_files[-1])
    with open(latest, "rb") as fh:
        js = fh.read().decode(errors="replace")
    print(f"Latest: {proj_files[-1]} ({len(js)} bytes)")
    for c in ["onBeforeRouteLeave", "beforeRouteLeave", "_alive", "#181826", "focus-within", "bg-"]:
        found = c in js
        print(f"  {'✅' if found else '❌'} {c}")

print("\nDone")