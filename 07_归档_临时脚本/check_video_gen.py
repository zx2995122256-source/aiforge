import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Get OiioiiPool generate_video function
stdin, stdout, stderr = client.exec_command(
    'grep -n "reference_video\|def generate_video\|ref_video" /home/ubuntu/oiioii/api/server.py 2>/dev/null | head -10',
    timeout=10
)
print(stdout.read().decode()[:500])

# Get the generate_video function
stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
import sys
with open('/home/ubuntu/oiioii/api/server.py') as f:
    content = f.read()
# Find generate_video function
import re
match = re.search(r'async def generate_video.*?\n(?:    .*\n)*', content, re.DOTALL)
if match:
    lines = match.group(0).split(chr(10))
    for l in lines[:40]:
        print(l)
" ''',
    timeout=10
)
print(stdout.read().decode()[:1500])

client.close()