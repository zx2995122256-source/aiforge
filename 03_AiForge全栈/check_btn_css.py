import urllib.request, re
r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
css_matches = re.findall(r'href="([^"]+\.css)"', html)
if css_matches:
    r2 = urllib.request.urlopen(f"http://localhost:7862{css_matches[0]}")
    css = r2.read().decode()
    # Search for button-related styles
    for keyword in ["btn-primary", "btn-secondary", ".btn-primary", ".btn-secondary", "btn {", "btn.", "\.btn"]:
        idx = css.find(keyword.replace("\.", ""))
        if idx >= 0:
            print(f"FOUND '{keyword}' at position {idx}")
            print(css[idx:idx+200])
            print("---")
        else:
            print(f"NOT FOUND: '{keyword}'")
    # Check what classes exist
    classes = re.findall(r'\.([a-zA-Z][\w-]+)\s*\{', css)
    button_classes = [c for c in classes if 'btn' in c.lower()]
    print(f"\nButton classes in CSS: {button_classes}")
    # Check input/glass classes
    target = ["glass-card", "input-field", "select-field", "shimmer"]
    for t in target:
        print(f"  {t}: {'✅' if t in css else '❌'}")
