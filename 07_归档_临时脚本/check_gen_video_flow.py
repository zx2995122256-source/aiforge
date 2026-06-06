import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check how _run_task uses reference_video for video
stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
with open('/home/ubuntu/oiioii/core/engine.py') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'generate_video' in line or 'ref_video' in line or 'reference_video' in line or 'hogi://' in line:
        print(f'{i+1}: {line.rstrip()}')
        # Also print next 5 lines
        for j in range(i+1, min(i+6, len(lines))):
            print(f'  {j+1}: {lines[j].rstrip()}')
        print()
" ''',
    timeout=10
)
print(stdout.read().decode()[:2000])

# Also check client.generate_video
stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
with open('/home/ubuntu/oiioii/core/core/client.py') as f:
    content = f.read()
import re
idx = content.find('def generate_video')
print(content[idx:idx+1500])
" ''',
    timeout=10
)
print("\n=== Client generate_video ===")
print(stdout.read().decode()[:1500])

client.close()