import urllib.request, re

# Check page renders
r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()

# Check Vue app mounts
has_app = '#app' in html and 'id="app"' in html
print(f"Vue app mount point: {'✅' if has_app else '❌'}")

# Login page components  
has_login = 'login' in html.lower() or '登录' in html
print(f"Login content: {'✅' if has_login else '❌'}")

# Check CSS actually loaded (look at rendered CSS class names)
css_matches = re.findall(r'href="([^"]+\.css)"', html)
if css_matches:
    main_css = css_matches[0]
    r2 = urllib.request.urlopen(f"http://localhost:7862{main_css}")
    css = r2.read().decode()
    
    # Check for actual class name in compiled CSS
    checks = [
        ("--border-color", "Old variable border-color"),
        ("--bg-card", "Old variable bg-card"),
        ("--bg-elevated", "Old variable bg-elevated"),
        ("--accent", "Variable accent"),
        (".btn-primary", "Class btn-primary"),
        (".glass-card", "Class glass-card"),
        (".input-field", "Class input-field"),
        (".shimmer", "NEW: shimmer skeleton"),
        ("shimmer-move", "NEW: shimmer animation"),
        ("prefers-reduced-motion", "NEW: reduced motion"),
    ]
    for keyword, label in checks:
        found = keyword in css
        marker = '✅' if found else '❌'
        print(f"  {marker} {label}")

    # Check the bg color
    if "#0b0b12" in css:
        print("  ✅ bg color: #0b0b12")
    else:
        print("  ❌ bg color NOT #0b0b12")
    
    print(f"\nCSS file size: {len(css)} bytes")
else:
    print("❌ No CSS file found in HTML")

# Check full HTML for any useful indicators
print(f"\nHTML size: {len(html)} bytes")
print(f"HTML body: {html[:500]}...")