import urllib.request, re
r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
css_match = re.findall(r'href="([^"]+\.css)"', html)
if css_match:
    r2 = urllib.request.urlopen(f"http://localhost:7862{css_match[0]}")
    css = r2.read().decode()
    
    checks = [
        ("text-white/", "Force text-white override"),
        ("bg-white/", "Force bg-white override"),
        ("border-white/", "Force border-white override"),
        ("!important", "Has !important rules"),
        ("0.78", "Text forced to 0.78 opacity"),
        ("0.08", "Bg forced to 0.08"),
        ("0.15", "Border forced to 0.15"),
        (".lbl", "lbl class"),
    ]
    for kw, label in checks:
        print(f"  {'✅' if kw in css else '❌'} {label}")

    # Count total !important rules
    imp_count = css.count("!important")
    print(f"\n  Total !important rules: {imp_count}")
    print(f"  CSS size: {len(css)} bytes")
else:
    print("❌ No CSS found")