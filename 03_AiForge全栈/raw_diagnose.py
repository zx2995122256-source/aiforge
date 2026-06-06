import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
css_match = re.findall(r'href="([^"]+\.css)"', html)
if css_match:
    r2 = urllib.request.urlopen(f"http://localhost:7862{css_match[0]}")
    css = r2.read().decode()
    
    # Raw search for ANY text-white pattern
    for pattern in ["text-white", "rgba(255,255,255", "rgb(255 255 255", "--text-", "white\\/"]:
        count = css.count(pattern)
        print(f"'{pattern}' found {count} times")
    
    # Show all unique rgba values
    rgba_255 = re.findall(r'rgba\(255,\s*255,\s*255,\s*[\d.]+\)', css)
    for v in sorted(set(rgba_255)):
        print(f"  TEXT RGBA: {v}")
    
    rgb_255 = re.findall(r'rgb\(255\s+255\s+255\s*/\s*[\d.]+\)', css)
    for v in sorted(set(rgb_255)):
        print(f"  TEXT RGB: {v}")
    
    # Check for escaped class names
    for kw in ["text-white", "bg-white", "border-white"]:
        idx = css.find(kw)
        if idx >= 0:
            # Show surrounding context
            start = max(0, idx - 5)
            end = min(len(css), idx + 60)
            snippet = css[start:end]
            print(f"\n'{kw}' snippet: {repr(snippet)}")
            break
    
    # Check for lbl class
    if ".lbl" in css:
        idx = css.find(".lbl")
        print(f"\n.lbl found: {css[idx:idx+100]}")
    else:
        print("\n.lbl NOT in CSS (it's in Project.vue scoped style, not global)")
    
    # Find the actual variable values
    for var in ["--text-primary", "--text-secondary", "--text-muted", "--bg-card", "--border-color", "--accent"]:
        idx = css.find(var)
        if idx >= 0:
            # Get the full value by looking for the next ;
            val_start = css.find(":", idx) + 1
            val_end = css.find(";", val_start)
            val = css[val_start:val_end].strip()
            print(f"\n{var} -> {val}")