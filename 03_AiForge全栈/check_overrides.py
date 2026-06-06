import urllib.request, re
r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
css_match = re.findall(r'href="([^"]+\.css)"', html)
if css_match:
    r2 = urllib.request.urlopen(f"http://localhost:7862{css_match[0]}")
    css = r2.read().decode()
    
    # Show the actual text-white/ override block
    idx = css.find("text-white/")
    if idx >= 0:
        start = css.rfind("[data-theme", 0, idx)
        end = css.find("}\n\n", idx)
        if end == -1:
            end = css.find("}\n", idx + 50) + 1
        print("OVERRIDE BLOCK:")
        print(css[start:end])
    
    # Count actual rgba(255,255,255,X) occurrences  
    matches = re.findall(r'color:\s*rgba\(255,\s*255,\s*255,\s*[\d.]+\)', css)
    print(f"\ncolor rgba values: {len(matches)}")
    for m in sorted(set(matches)):
        print(f"  {m}")
    
    matches2 = re.findall(r'color:\s*rgba\(\d+,\s*\d+,\s*\d+,\s*[\d.]+\)', css)
    print(f"\nAll color rgba values: {len(matches2)}")
    for m in sorted(set(matches2)):
        print(f"  {m}")
    
    print(f"\nTotal CSS: {len(css)} bytes")