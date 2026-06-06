import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

stdin, stdout, stderr = client.exec_command('echo "✅ SSH连接成功"; uname -a; uptime', timeout=10)
print(stdout.read().decode()[:500])

# check services
stdin, stdout, stderr = client.exec_command('systemctl is-active aiforge oiioii 2>/dev/null; echo "---"; ss -tlnp | grep -E "7861|7862"', timeout=10)
print(stdout.read().decode()[:300])

client.close()