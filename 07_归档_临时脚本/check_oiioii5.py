import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check what endpoints are available
stdin, stdout, stderr = client.exec_command('curl -s http://127.0.0.1:7861/openapi.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(list(d.get(\"paths\",{}).keys()), indent=2))" 2>/dev/null')
print("Available Oiioii endpoints:")
print(stdout.read().decode()[:2000])

client.close()