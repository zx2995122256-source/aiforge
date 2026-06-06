#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', password='zx4579561.', timeout=15)

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

# Try to find the Oiioii frontend JS and look for API endpoints
script = """
import requests, re

# Get the main page
r = requests.get('https://www.oiioii.ai/', timeout=15)
html = r.text

# Find JS files
js_files = re.findall(r'src="([^"]*\\.js[^"]*)"', html)
print(f'JS files: {js_files[:5]}')

# Try to find API endpoints in the main JS
for js_url in js_files[:3]:
    if not js_url.startswith('http'):
        js_url = f'https://www.oiioii.ai{js_url}'
    try:
        r2 = requests.get(js_url, timeout=15)
        # Find API paths
        api_paths = re.findall(r'["\\']/(\\w+/\w+[^"\\'\\s]{5,40})["\\']', r2.text)
        unique = list(set(api_paths))[:30]
        if unique:
            print(f'\\nFrom {js_url[:60]}:')
            for p in sorted(unique):
                print(f'  /{p}')
    except:
        pass
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_scrape_api.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_scrape_api.py')
print(out[:3000])

ssh.close()
