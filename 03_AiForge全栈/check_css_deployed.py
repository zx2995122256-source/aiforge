import urllib.request, re

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
css_matches = re.findall(r'href="([^"]+\.css)"', html)
print("CSS files referenced:")
for c in css_matches:
    print(f"  {c}")

# Check first 10 lines of main CSS
if css_matches:
    main_css = css_matches[0]
    r2 = urllib.request.urlopen(f"http://localhost:7862{main_css}")
    css_content = r2.read().decode()
    # Check for new theme variables
    if "--bg-elevated-1" in css_content:
        print("\n✅ NEW theme system detected (--bg-elevated-1 present)")
    else:
        print("\n❌ OLD theme system (no --bg-elevated-1)")
    if "--color-success" in css_content:
        print("✅ Semantic colors present (--color-success)")
    if "--accent: #818cf8" in css_content:
        print("✅ New accent color #818cf8 (indigo)")
    if ".btn-primary" in css_content:
        print("✅ New button system (.btn-primary found)")
    if "shimmer" in css_content:
        print("✅ Shimmer skeleton animation present")
    print(f"\nCSS file size: {len(css_content)} bytes")
