import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

cmds = [
    'curl -s http://127.0.0.1:7861/api/tasks?limit=15',
    'journalctl -u oiioii --no-pager -n 200 2>/dev/null | tail -80',
    'cat /home/ubuntu/oiioii/core/client.py | grep -n "_refs_to_data_urls\\|upload_to_oiioii\\|reference_images\\|reference_video\\|videoUrl\\|images.*refs" | head -20',
    'cat /home/ubuntu/oiioii/core/engine.py | grep -n "manual_refresh\\|reference_images\\|reference_video\\|video_ref" | head -20',
    'cat /home/ubuntu/oiioii/core/client.py | sed -n "156,200p"',
]

for cmd in cmds:
    print(f'>>> {cmd[:100]}')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()[:1500]
    err = stderr.read().decode()[:300]
    if out.strip():
        print(out)
    if err.strip():
        print(f'STDERR: {err}')
    print('---')

ssh.close()
