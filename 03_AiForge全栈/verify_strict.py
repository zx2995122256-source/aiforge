import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
css_match = re.findall(r'href="([^"]+\.css)"', html)
css = urllib.request.urlopen(f"http://localhost:7862{css_match[0]}").read().decode()

# Check all !important rules with context
idx = 0
count = 0
while True:
    idx = css.find("!important", idx)
    if idx == -1:
        break
    start = css.rfind("{", max(0, idx - 200), idx)
    if start == -1:
        start = max(0, idx - 100)
    snippet = css[start:idx+30].replace("\n", " ").strip()
    print(f"#{count}: ...{snippet[-100:]}")
    idx += 20
    count += 1
print(f"\nTotal: {count}")

# Check if GLOBAL FORCE section is gone
if "GLOBAL FORCE" in css:
    print("\n❌ GLOBAL FORCE section STILL PRESENT")
else:
    print("\n✅ GLOBAL FORCE section removed")

# Check specific destructive selectors
bad_selectors = [
    '[class*="text-white/"]',
    '[class*="bg-white/"]',
    '[class*="bg-black/"]',
    '[class*="border-white/"]',
]
for sel in bad_selectors:
    idx = css.find(sel)
    if idx >= 0 and "!important" in css[idx-50:idx+200]:
        print(f"❌ {sel} still has !important")
    else:
        print(f"✅ {sel} !important removed")

# Check if onBeforeRouteLeave is in Project JS
js_match = re.findall(r'src="([^"]+Project-[^"]+\.js)"', html)
if js_match:
    print(f"\n✅ Project JS: {js_match[0]}")
    js = urllib.request.urlopen(f"http://localhost:7862{js_match[0]}").read().decode(errors="replace")
    for c in ["_alive", "onBeforeRouteLeave"]:
        print(f"  {'✅' if c in js else '❌'} {c}")

print("\nDone")