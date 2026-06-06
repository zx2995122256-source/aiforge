import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Get the full client.py
stdin, stdout, stderr = client.exec_command(
    'cat /home/ubuntu/oiioii/core/core/client.py 2>/dev/null || cat /home/ubuntu/oiioii/core/client.py 2>/dev/null',
    timeout=10
)
content = stdout.read().decode()

# Find the upload_video_file and upload_to_oiioii functions
idx = content.find("def upload_video_file")
if idx >= 0:
    print(content[idx:idx+2000])

client.close()