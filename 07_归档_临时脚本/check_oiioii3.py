import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

stdin, stdout, stderr = client.exec_command('grep -n "route\|router\|api_" /home/ubuntu/oiioii/main.py 2>/dev/null | head -30')
endpoints = stdout.read().decode()
print("Oiioii endpoints:")
print(endpoints)

stdin, stdout, stderr = client.exec_command('grep -n "total_points\|total_accounts\|pool" /home/ubuntu/oiioii/main.py 2>/dev/null | head -20')
status_lines = stdout.read().decode()
print("Status lines:")
print(status_lines)

client.close()