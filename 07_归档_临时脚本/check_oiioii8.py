import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Search for endpoint defs
stdin, stdout, stderr = client.exec_command("grep -n '@app\\.\\|def \\|pool\\.' /home/ubuntu/oiioii/api/server.py")
print(stdout.read().decode()[:2000])

client.close()