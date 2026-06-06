import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Read the server.py
stdin, stdout, stderr = client.exec_command('cat -n /home/ubuntu/oiioii/api/server.py', timeout=10)
lines = stdout.read().decode().split('\n')

# Find the problematic duplicate section
# Lines 100-125 approximately
for line in lines[99:130]:
    print(line)

client.close()