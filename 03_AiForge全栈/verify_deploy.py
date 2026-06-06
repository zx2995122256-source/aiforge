import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
code = r.status
print(f"HTTP status: {code}")

css_matches = re.findall(r'href="([^"]+\.css)"', html)
print(f"CSS files: {css_matches}")

has_btn = "btn-primary" in html
has_glass = "glass-card" in html
has_input = "input-field" in html
print(f"btn-primary in HTML: {has_btn}")
print(f"glass-card in HTML: {has_glass}")
print(f"input-field in HTML: {has_input}")

# Check CSS content for legacy vars
if css_matches:
    main_css = css_matches[0]
    r2 = urllib.request.urlopen(f"http://localhost:7862{main_css}")
    css = r2.read().decode()
    checks = [
        ("--border-color", "LEGACY border-color OK"),
        ("--bg-card", "LEGACY bg-card OK"),
        ("btn-primary {", "LEGACY btn-primary standalone OK"),
        ("btn-secondary {", "LEGACY btn-secondary OK"),
    ]
    print()
    for keyword, msg in checks:
        found = keyword in css
        print(f"  {'✅' if found else '❌'} {msg}")
    print(f"\nCSS size: {len(css)} bytes")