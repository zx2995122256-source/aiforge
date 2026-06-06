import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

stdin, stdout, stderr = client.exec_command('ls -la /home/ubuntu/oiioii/')
print("Oiioii dir:")
print(stdout.read().decode()[:500])

stdin, stdout, stderr = client.exec_command('find /home/ubuntu/oiioii -name "*.py" | head -30')
print("Oiioii files:")
print(stdout.read().decode()[:500])

stdin, stdout, stderr = client.exec_command('grep -r "route\|@router\|api_router\|app.include" /home/ubuntu/oiioii/api/server.py 2>/dev/null | head -30')
print("Routes:")
print(stdout.read().decode()[:1000])

client.close()