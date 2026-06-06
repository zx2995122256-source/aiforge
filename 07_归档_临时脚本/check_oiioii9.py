import paramiko, json

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

stdin, stdout, stderr = client.exec_command('curl -s http://127.0.0.1:7861/api/pool/status')
data = stdout.read().decode()
print("Pool Status:")
try:
    d = json.loads(data)
    print(json.dumps(d, indent=2, ensure_ascii=False))
except:
    print(data[:2000])

# Also check how many coins/models
stdin, stdout, stderr = client.exec_command('curl -s http://127.0.0.1:7861/api/tasks?limit=5 | head -c 200')
print("\nRecent tasks:")
print(stdout.read().decode()[:200])

client.close()