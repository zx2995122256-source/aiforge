import sys, json, os

# Check server dist vs local dist
local_js = r"c:\Users\Administrator\Documents\锤子Aicg\03_AiForge全栈\frontend\dist\assets"

# Get all Project-related files in local dist
for f in os.listdir(local_js):
    if "Project" in f and f.endswith(".js"):
        fp = os.path.join(local_js, f)
        js = open(fp, "rb").read().decode(errors="replace")
        print(f"本地 {f} ({len(js)}B)")
        print(f"  #252540: {'#252540' in js}")
        print(f"  onActivated: {'onActivated' in js}")
        print(f"  onDeactivated: {'onDeactivated' in js}")
        print(f"  #7c3aed: {'#7c3aed' in js}")
        print(f"  #181826: {'#181826' in js}")

# Also check local dist html
print()
html_path = r"c:\Users\Administrator\Documents\锤子Aicg\03_AiForge全栈\frontend\dist\index.html"
html = open(html_path, "r", encoding="utf-8").read()
# Extract script refs
import re
scripts = re.findall(r'src="(/assets/[^"]+)"', html)
styles = re.findall(r'href="(/assets/[^"]+\.css)"', html)
print(f"本地 dist index.html:")
for s in scripts: print(f"  script: {s}")
for c in styles: print(f"  style:  {c}")