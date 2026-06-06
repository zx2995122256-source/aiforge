import sys, re
sys.path.insert(0, '/home/ubuntu/aiforge/backend')
import admin

html = admin.ADMIN_HTML

# Find the inline script (not the tailwind one)
idx = html.find('<script>\n')
if idx < 0:
    idx = html.find('<script>\r\n')
if idx < 0:
    # Try finding <script> followed by newline
    for m in re.finditer(r'<script>', html):
        after = html[m.end():m.end()+20]
        if not after.startswith('src='):
            idx = m.start()
            break

if idx >= 0:
    close_idx = html.find('</script>', idx)
    js = html[idx+8:close_idx]
    print(f"JS length: {len(js)} chars")

    # Write to file
    with open('/tmp/admin_check.js', 'w') as f:
        f.write(js)

    # Check with node
    import subprocess
    result = subprocess.run(['node', '--check', '/tmp/admin_check.js'], capture_output=True, text=True)
    if result.returncode == 0:
        print("JS syntax: OK")
    else:
        print(f"JS syntax ERROR: {result.stderr}")
else:
    print("Could not find inline script tag")
