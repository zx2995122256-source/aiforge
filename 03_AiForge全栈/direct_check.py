import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()

# Direct: check if my CSS changes are in the compiled CSS
css_match = re.findall(r'href="([^"]+\.css)"', html)
if css_match:
    css = urllib.request.urlopen(f"http://localhost:7862{css_match[0]}").read().decode()
    
    # Search for the ACTUAL values
    search_for = ["#eeeeef", "#b8b8c0", "#909098", "#181826"]
    for s in search_for:
        count = css.count(s)
        print(f"'{s}' in CSS: {count} times")
    
    # Full search for all hex colors like #... that could be text colors
    hex_colors = re.findall(r'#[0-9a-fA-F]{6}', css)
    hex_set = set(hex_colors)
    print(f"\nTotal unique hex colors in CSS: {len(hex_set)}")
    # Show actual hex colors sorted
    for c in sorted(hex_set)[:30]:
        print(f"  {c}")

# Check JS Project file
js_match = re.findall(r'src="([^"]+\.js)"', html)
print(f"\nTotal JS files: {len(js_match)}")
for j in js_match:
    if "Project" in j:
        print(f"  ✅ Project JS: {j}")
        js = urllib.request.urlopen(f"http://localhost:7862{j}").read().decode(errors="replace")
        # Search for solid colors
        for c in ["#181826", "#3a3a52", "_alive", "onBeforeRouteLeave"]:
            found = c in js
            print(f"    {'✅' if found else '❌'} {c}")

print("\nDone")