import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Try running the app directly to see the import error
stdin, stdout, stderr = client.exec_command('cd /home/ubuntu/aiforge/backend && python3 -c "from main import app; print(\'OK\')" 2>&1')
out = stdout.read().decode()
err = stderr.read().decode()
print("out:", out[:1000])
print("err:", err[:2000])

client.close()
