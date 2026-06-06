import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

cmds = [
    'journalctl -u oiioii --no-pager --since "5 min ago" 2>/dev/null | grep -i "poll\\|asset\\|Task #392\\|FOUND\\|TIMEOUT\\|token\\|switching" | tail -30',
    'curl -s http://127.0.0.1:7861/api/task/392',
]

for cmd in cmds:
    print(f'>>> {cmd[:120]}')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()[:1500]
    if out.strip():
        print(out)
    print('---')

ssh.close()
