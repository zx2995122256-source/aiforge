import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

stdin, stdout, stderr = client.exec_command(
    'sed -n "255,290p" /home/ubuntu/oiioii/core/core/client.py 2>/dev/null || sed -n "255,290p" /home/ubuntu/oiioii/core/client.py',
    timeout=10
)
print(stdout.read().decode()[:1500])

client.close()