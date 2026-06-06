import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

stdin, stdout, stderr = client.exec_command('cat /home/ubuntu/oiioii/api/server.py', timeout=10)
content = stdout.read().decode()

# Find upload-size related code
import re
for line in content.split('\n'):
    if any(x in line.lower() for x in ['upload', 'max', 'size', 'nginx', 'body', 'limit', 'app.', 'uvicorn']):
        print(line)

print("\n=== Last 20 lines ===")
lines = content.split('\n')
for line in lines[-20:]:
    print(line)

stdin, stdout, stderr = client.exec_command('cat /home/ubuntu/oiioii/config.ini', timeout=10)
print("\n=== config.ini ===")
print(stdout.read().decode()[:500])

client.close()