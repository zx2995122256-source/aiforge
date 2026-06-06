import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()

css_match = re.findall(r'href="([^"]+\.css)"', html)
css_name = css_match[0] if css_match else "NONE"
print(f"Serving CSS: {css_name}")

css = urllib.request.urlopen(f"http://localhost:7862{css_name}").read().decode()

# Check if my Project.vue changes are deployed by looking for solid colors
js_matches = re.findall(r'src="([^"]+Project-[^"]+\.js)"', html)
if js_matches:
    js_name = js_matches[0]
    print(f"Serving Project JS: {js_name}")
    js = urllib.request.urlopen(f"http://localhost:7862{js_name}").read().decode(errors="replace")
    
    # Check for the Agent dialog solid colors I wrote
    checks = {
        "#181826": "Agent solid bg color",
        "#3a3a52": "Agent border color",
        "onBeforeRouteLeave": "route leave guard",
        "_alive": "alive flag",
        "bg-transparent": "Agent input transparent bg",
        "placeholder-white/35": "placeholder opacity",
    }
    for val, label in checks.items():
        found = val in js or val.replace("#","") in js
        print(f"  {'✅' if found else '❌'} {label} ({val})")

# Check if style.css has my variable tweaks
for var in ["--text-primary", "--text-secondary", "--text-muted"]:
    idx = css.find(var)
    if idx >= 0:
        vs = css.find(":", idx)+1
        ve = css.find(";", vs)
        val = css[vs:ve].strip()
        print(f"  CSS {var} = {val}")

# Check dist file timestamp  
from pathlib import Path
import os
dist_css = sorted(Path("/home/ubuntu/aiforge/dist/assets").glob("index-*.css"), key=os.path.getmtime)
if dist_css:
    import time
    mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(dist_css[-1])))
    print(f"\nLatest dist CSS file: {dist_css[-1].name} (modified {mtime})")

print("\nDone")