import subprocess, json, urllib.request, re

# 1. Check what HTML the server is serving right now
r = urllib.request.urlopen("http://localhost:7862/")
html = r.read().decode()
css_href = re.findall(r'href="([^"]+\.css)"', html)
print(f"HTML references CSS: {css_href[0] if css_href else 'NONE'}")

# 2. Check the actual file on disk
r2 = urllib.request.urlopen(f"http://localhost:7862{css_href[0]}")
css = r2.read().decode()

checks = [
    ("--text-primary", "primary"),
    ("--text-secondary", "secondary"),
    ("--text-muted", "muted"),
    ("--border-color", "border"),
    ("#0b0b12", "bg color 0b0b12"),
    ("#eeeeef", "text bright"),
    ("#b8b8c0", "secondary bright"),
    ("#909098", "muted bright"),
    ("btn-primary", "btn class"),
]
print("\nWhat's IN the live CSS:")
for kw, label in checks:
    print(f"  {'✅' if kw in css else '❌'} {label}")

# 3. Check if the service is the right one
print(f"\nService PID check:")
r3 = subprocess.run(
    ["ps", "aux"],
    capture_output=True, text=True
)
for line in r3.stdout.split("\n"):
    if "uvicorn main:app" in line:
        print(f"  ✅ aiforge backend running: {line.strip()}")
    elif "7862" in line and "python3" in line:
        print(f"  Port 7862 process: {line.strip()}")

# 4. Check dist/index.html
import os
idx_path = "/home/ubuntu/aiforge/dist/index.html"
if os.path.exists(idx_path):
    with open(idx_path) as f:
        idx_content = f.read()
    idx_css = re.findall(r'href="([^"]+\.css)"', idx_content)
    print(f"\ndist/index.html references: {idx_css[0] if idx_css else 'NONE'}")

print("\nDone")