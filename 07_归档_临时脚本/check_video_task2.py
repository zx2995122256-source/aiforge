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
# Find task_type video handling  
idx = content.find('task_type')
# Print from 100 chars before to 2000 chars after
start = max(0, idx - 100)
print(content[start:start+2500])
" ''',
    timeout=10
)
print(stdout.read().decode()[:2500])

client.close()