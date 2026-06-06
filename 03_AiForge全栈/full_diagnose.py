import urllib.request, re, json

BASE = "http://localhost:7862"

# 1. Get the index.html
r = urllib.request.urlopen(f"{BASE}/")
html = r.read().decode()

# 2. Login to get token for API access
login_data = json.dumps({"email": "sci_test@aiforge.ai", "password": "sci2025pw"}).encode()
req = urllib.request.Request(f"{BASE}/api/auth/login", data=login_data, headers={"Content-Type": "application/json"})
rr = urllib.request.urlopen(req, timeout=10)
token = json.loads(rr.read())["token"]

# 3. Check Agent input in HTML of Project page
req2 = urllib.request.Request(f"{BASE}/api/project/list", headers={"Authorization": f"Bearer {token}"})
projects = json.loads(urllib.request.urlopen(req2, timeout=10).read())
print(f"Projects: {len(projects)}")
if projects:
    pid = projects[0]["id"]
    req3 = urllib.request.Request(f"{BASE}/api/project/{pid}", headers={"Authorization": f"Bearer {token}"})
    p = json.loads(urllib.request.urlopen(req3, timeout=10).read())
    print(f"Project #{pid}: assets={len(p.get('assets',[]))} segs={len(p.get('segments',[]))}")

# 4. Check CSS for Agent input rule
css_match = re.findall(r'href="([^"]+\.css)"', html)
css_url = f"{BASE}{css_match[0]}"
css = urllib.request.urlopen(css_url).read().decode()

# Check for the override rules
print(f"\nCSS file: {css_match[0]}")
print(f"Contains 'text-white/' override: {'text-white/' in css}")
print(f"Contains input[class*=\"bg-white/\"]: {'input[class*=bg-white' in css}")
print(f"Contains !important: {css.count('!important')} times")

# Check for Agent input related CSS
# The Agent input is in Project.vue's scoped style, so it will have a data-v- hash
agent_check = "placeholder=\"" in html  # placeholder text
print(f"Has placeholder='和Agent说...': {'和Agent说' in html}")

# Check what classes the Agent input would have
print(f"\nLooking for Agent input in CSS...")
for kw in ["flex-1 bg-white", "rounded-lg px-3 py-1", "placeholder-white"]:
    if kw in css:
        # Find context
        idx = css.find(kw)
        start = max(0, idx - 30)
        end = min(len(css), idx + 100)
        print(f"  FOUND '{kw}': {css[start:end]}")
    else:
        print(f"  NOT FOUND '{kw}'")

# Check for the scoped style in Project's JS
js_matches = re.findall(r'src="([^"]+Project-[^"]+\.js)"', html)
if js_matches:
    js_url = f"{BASE}{js_matches[0]}"
    js = urllib.request.urlopen(js_url).read().decode(errors='replace')
    print(f"\nProject JS: {js_matches[0]} ({len(js)} bytes)")
    
    # Look for scoped input class
    if "bg-white/[0.06]" in js:
        print("  ✅ bg-white/[0.06] found in JS (my change)")
    elif "bg-white/[0.02]" in js:
        print("  ❌ bg-white/[0.02] found (ORIGINAL - NOT UPDATED)")
    elif "bg-white/\\[0" in js:
        # escaped in JS
        for variant in ["0.02", "0.03", "0.06"]:
            if f"0.0{variant}" in js or f"0.{variant}" in js:
                print(f"  bg-white opacities found: 0.{variant}")
    else:
        # search for any bg-white pattern
        matches = re.findall(r'bg-white[^"\' ]+', js)
        if matches:
            print(f"  bg-white patterns: {set(matches[:5])}")
    
    if "lbl" in js:
        lbl_idx = js.find("lbl")
        if lbl_idx >= 0:
            print(f"  lbl found at pos {lbl_idx}")
            print(f"  Context: {js[lbl_idx-20:lbl_idx+80]}")
    
    # Check for Agent input  
    if "chatInput" in js:
        chat_idx = js.find("chatInput")
        print(f"  chatInput found at pos {chat_idx}")
        context = js[chat_idx:chat_idx+200]
        print(f"  Context: {context}")