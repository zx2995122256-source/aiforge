import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()

css_match = re.findall(r'href="([^"]+\.css)"', html)
if css_match:
    css = urllib.request.urlopen(f"http://localhost:7862{css_match[0]}").read().decode()
    print(f"CSS: {len(css)} bytes")
    
    # The Tailwind compiler converts rgba to hex: rgba(255,255,255,0.78) = #ffffffc7
    # rgba(255,255,255,0.08) = #ffffff14
    for c in ["#ffffffc7", "#ffffff14", "#ffffff26", "!important"]:
        print(f"  {'✅' if c in css else '❌'} {c}")
    
    # Also check for the actual important rules count
    print(f"\n  Total !important: {css.count('!important')}")

    # Check Project JS for the Agent input
    js_match = re.findall(r'src="([^"]+Project-[^"]+\.js)"', html)
    if js_match:
        js = urllib.request.urlopen(f"http://localhost:7862{js_match[0]}").read().decode(errors="replace")
        for c in ["#181826", "#3a3a52", "onBeforeRouteLeave"]:
            found = c in js
            print(f"  {'✅' if found else '❌'} {c} in Project JS")

print("Done")