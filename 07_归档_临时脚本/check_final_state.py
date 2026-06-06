import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check the current file
stdin, stdout, stderr = client.exec_command('grep -n "upload_video_ref\|upload_video_reference" /home/ubuntu/oiioii/api/server.py', timeout=10)
print("upload_video_ref references:")
print(stdout.read().decode()[:300])

# Get the full function around that
stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
with open('/home/ubuntu/oiioii/api/server.py') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'upload_video_ref' in l or 'upload_video_reference' in l:
        for j in range(i-2, min(i+15, len(lines))):
            print(f'{j+1}: {lines[j].rstrip()}')
        print('---')
" ''',
    timeout=10
)
print(stdout.read().decode()[:1000])

client.close()