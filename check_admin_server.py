import re
with open('/root/aiforge/admin.py','r') as f:
    content = f.read()
# Find the script content - skip tailwind script tag
start = content.find('<script>', content.find('</style>'))
end = content.find('</script>', start + 8)
if start > 0 and end > 0:
    js_start = start + len('<script>')
    js = content[js_start:end]
    with open('/tmp/admin_check.js','w') as out:
        out.write(js)
    print('JS extracted, length:', len(js))
else:
    print('Script tags not found, start=', start, 'end=', end)
