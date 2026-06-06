import re
with open('/root/aiforge/admin.py','r') as f:
    c = f.read()
s = c.find('<script>', c.find('</style>'))
e = c.find('</script>', s + 8)
if s > 0 and e > 0:
    js = c[s+8:e]
    with open('/tmp/admin_check.js','w') as out:
        out.write(js)
    print('JS length:', len(js))
else:
    print('NOT FOUND')
