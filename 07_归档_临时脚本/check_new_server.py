import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check OiioiiPool errors
stdin, stdout, stderr = client.exec_command(
    'sudo journalctl -u oiioii --since "1 min ago" --no-pager 2>/dev/null | python3 -c "import sys;lines=sys.stdin.read().split(chr(10));[print(l) for l in lines[-20:] if l]"',
    timeout=10
)
print(stdout.read().decode()[:1500])

# Check if the server.py is correct  
stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
with open('/home/ubuntu/oiioii/api/server.py') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'upload_video_reference' in l or 'REFS_DIR' in l or 'hashlib' in l or 'public_url' in l:
        print(f'{i+1}: {l.rstrip()}')
" ''',
    timeout=10
)
print("\n=== New code lines ===")
print(stdout.read().decode()[:800])

client.close()