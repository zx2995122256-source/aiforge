import urllib.request, re, json

r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
css_match = re.findall(r'href="([^"]+\.css)"', html)
css = urllib.request.urlopen(f"http://localhost:7862{css_match[0]}").read().decode()

# Show ALL important rules with context
idx = 0
count = 0
while True:
    idx = css.find("!important", idx)
    if idx == -1:
        break
    start = css.rfind("}", max(0, idx - 500), idx)
    if start == -1:
        start = max(0, idx - 200)
    end = css.find("}", idx)
    if end == -1:
        end = idx + 50
    print(f"\n--- !important rule #{count} ---")
    print(f"Position: {idx}")
    print(css[start:end+1][:300])
    idx = end + 1
    count += 1

print(f"\n\nTotal !important: {count}")

# Check if the input override exists in the raw source
check_str = "input[class*="
if check_str in css:
    i = css.find(check_str)
    print(f"\ninput override found at {i}: {css[i:i+200]}")
else:
    print(f"\ninput override NOT FOUND in compiled CSS!")
    # Search for the actual text
    for s in ["input[", "data-theme=deepspace] input", "input{background", "background-color:#ffffff1a"]:
        if s in css:
            i = css.find(s)
            print(f"  Found '{s}' at {i}: {css[max(0,i-30):i+100]}")
        else:
            print(f"  NOT FOUND '{s}'")