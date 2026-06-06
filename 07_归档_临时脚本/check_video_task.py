import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
with open('/home/ubuntu/oiioii/core/engine.py') as f:
    content = f.read()
import re
# Find the video section after reference_video in _run_task
idx = content.find('if task_type == \"video\"')
print(content[idx:idx+2000])
" ''',
    timeout=10
)
print(stdout.read().decode()[:2000])

client.close()