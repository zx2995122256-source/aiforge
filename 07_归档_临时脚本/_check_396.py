import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

cmds = [
    # Full engine log for task 396
    'journalctl -u oiioii --no-pager --since "5 min ago" 2>/dev/null | grep -v "GET /api/task" | grep -v "pool/register\\|pool/status" | tail -40',
    # Check task 396 details
    'curl -s http://127.0.0.1:7861/api/task/396',
    # Check if the no-ref baseline test started
    'cat /tmp/test_clean.log | tail -5',
]

for cmd in cmds:
    print(f'>>> {cmd[:120]}')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()[:2000]
    if out.strip():
        print(out)
    print('---')

ssh.close()
