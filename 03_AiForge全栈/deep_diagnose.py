import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
css_match = re.findall(r'href="([^"]+\.css)"', html)
if css_match:
    r2 = urllib.request.urlopen(f"http://localhost:7862{css_match[0]}")
    css = r2.read().decode()
    
    # Check for specific Tailwind opacity classes
    checks = [
        "text-white\\/30",
        "text-white\\/20", 
        "text-white\\/10",
        "bg-white\\/\\[0\\.02\\]",
        "bg-white\\/\\[0\\.04\\]",
        "bg-white\\/\\[0\\.06\\]",
        "border-white\\/\\[0\\.04\\]",
        "border-white\\/\\[0\\.06\\]",
        ".btn-primary",
        ".lbl",
        "shimmer",
    ]
    for c in checks:
        found = c.replace("\\", "\\\\") in css
        print(f"{'✅' if found else '❌'} {c}")

    # Search for rgba patterns to find actual text opacity values being used
    text_patterns = re.findall(r'rgba\(255,\s*255,\s*255,\s*0\.[0-9]+\)', css)
    bg_patterns = re.findall(r'background-color:\s*rgba\(255,\s*255,\s*255,\s*0\.[0-9]+\)', css)
    border_patterns = re.findall(r'border-color:\s*rgba\(255,\s*255,\s*255,\s*0\.[0-9]+\)', css)
    
    print(f"\nText opacity values: {set(text_patterns)}")
    print(f"Bg opacity values: {set(bg_patterns)}")
    print(f"Border opacity values: {set(border_patterns)}")
    
    # Check what variables the CSS uses
    var_checks = ["--text-primary", "--text-secondary", "--text-muted", "--accent", "--bg-card", "--bg-elevated"]
    for v in var_checks:
        idx = css.find(v)
        if idx >= 0:
            line = css[idx:idx+80].split(";")[0]
            print(f"  {v} = {line.split(':')[1].strip() if ':' in line else '?'}")
