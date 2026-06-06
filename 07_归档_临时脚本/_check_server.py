import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

cmds = [
    'systemctl is-active oiioii aiforge',
    'curl -s http://127.0.0.1:7861/api/pool/status | head -c 200',
    'ls -la /home/ubuntu/oiioii/data/output/refs/ 2>/dev/null | tail -10',
    'journalctl -u oiioii --no-pager -n 100 2>/dev/null | grep -i "ref\\|upload\\|_refs_to\\|hogi\\|error\\|fail\\|manualRefresh" | tail -30',
    'curl -s http://127.0.0.1:7861/api/tasks?limit=10 | python3 -c "import sys,json;tasks=json.load(sys.stdin).get(\'tasks\',[]);[print(f\'ID={t[\"id\"]} {t[\"type\"]} {t[\"model\"]} {t[\"status\"]} err={t.get(\"error\",\"\")[:50]}\') for t in tasks]"',
]

for cmd in cmds:
    print(f'>>> {cmd[:100]}')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()[:800]
    err = stderr.read().decode()[:300]
    if out.strip():
        print(out)
    if err.strip():
        print(f'STDERR: {err}')
    print('---')

ssh.close()
