import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

stdin, stdout, stderr = client.exec_command('ls -la /home/ubuntu/')
print("/home/ubuntu/:", stdout.read().decode()[:500])

stdin, stdout, stderr = client.exec_command('ls -la /home/ubuntu/aiforge/')
print("\naiforge/:", stdout.read().decode()[:500])

stdin, stdout, stderr = client.exec_command('ls -la /home/ubuntu/backend/')
print("\nbackend/:", stdout.read().decode()[:500])

stdin, stdout, stderr = client.exec_command('ls /home/ubuntu/aiforge/dist 2>/dev/null && echo "HAS DIST" || echo "NO DIST"')
print("\nDist check:", stdout.read().decode()[:100])

# Check service status
stdin, stdout, stderr = client.exec_command('sudo systemctl status aiforge --no-pager 2>/dev/null | head -5')
print("\nAiforge status:", stdout.read().decode()[:200])

stdin, stdout, stderr = client.exec_command('sudo systemctl status oiioii --no-pager 2>/dev/null | head -5')
print("Oiioii status:", stdout.read().decode()[:200])

# Check API 
stdin, stdout, stderr = client.exec_command('curl -s http://127.0.0.1:7862/api/gen/models | head -c 200')
print("\nAiForge API:", stdout.read().decode()[:200])

stdin, stdout, stderr = client.exec_command('curl -s http://127.0.0.1:7861/api/pool/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(d)"')
print("Oiioii API:", stdout.read().decode()[:200])

client.close()
