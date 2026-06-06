import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check OiioiiPool config
stdin, stdout, stderr = client.exec_command('''python3 -c "
import requests
# Check OiioiiPool app config - try to find max upload size
r = requests.get('http://127.0.0.1:7861/openapi.json', timeout=10)
spec = r.json()
print('Title:', spec.get('info', {}).get('title', ''))
print('Version:', spec.get('info', {}).get('version', ''))
# Look for any size limit params
paths = spec.get('paths', {})
for p, methods in paths.items():
    for m, details in methods.items():
        params = details.get('parameters', [])
        for param in params:
            if 'size' in param.get('name','').lower() or 'max' in param.get('name','').lower():
                print(f'{p} {m}: {param}')
        # Check requestBody
        rb = details.get('requestBody', {})
        content = rb.get('content', {})
        for ct, ct_details in content.items():
            schema = ct_details.get('schema', {})
            print(f'{p} {m}: schema keys={list(schema.keys())}')
" 2>&1''', timeout=10)
print(stdout.read().decode()[:500])

# Check uvicorn settings for OiioiiPool
stdin, stdout, stderr = client.exec_command('''systemctl cat oiioii 2>/dev/null | grep -i "max\|size\|limit" || echo "no limits found"''', timeout=10)
print("\n=== Service limits ===")
print(stdout.read().decode()[:500])

# Check if there's a config.py for OiioiiPool
stdin, stdout, stderr = client.exec_command('find /home/ubuntu/oiioii -name "config*" -o -name "*.py" | head -10', timeout=10)
print("\n=== OiioiiPool files ===")
print(stdout.read().decode()[:500])

# Check the main.py for upload size
stdin, stdout, stderr = client.exec_command('''grep -n "max_size\|MAX_SIZE\|upload.*size\|body.*limit\|max_body\|MAX_BODY" /home/ubuntu/oiioii/main.py 2>/dev/null || echo "not found at main.py"''', timeout=10)
print("\n=== Upload size check ===")
print(stdout.read().decode()[:500])

client.close()