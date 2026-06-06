import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

cmds = [
    # Check which account was used for task 392
    'python3 -c "import sqlite3;conn=sqlite3.connect(\'/home/ubuntu/oiioii/data/oiioii_pool.db\');cur=conn.execute(\'SELECT t.id,t.account_id,a.email,a.points_remaining,a.status FROM tasks t JOIN accounts a ON t.account_id=a.id WHERE t.id IN (389,390,391,392,393)\');[print(r) for r in cur.fetchall()]"',
    # Check current pool status - accounts with enough points
    'curl -s http://127.0.0.1:7861/api/pool/status | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\'total={d[\"total_accounts\"]} active={d[\"active_accounts\"]} pts={d[\"total_points\"]}\')"',
    # Check what the video ref actually was - the file
    'ls -la /home/ubuntu/oiioii/data/output/refs/vidref_1780293719_d86f3b01.mp4',
    # Check the full journal log for task 392
    'journalctl -u oiioii --no-pager --since "8 min ago" 2>/dev/null | grep "Task #392\\|392\\|video_ref\\|resolve\\|videoUrl\\|submit\\|generate_video\\|INSUFFICIENT" | head -20',
    # Check latest task statuses
    'curl -s http://127.0.0.1:7861/api/tasks?limit=5 | python3 -c "import sys,json;tasks=json.load(sys.stdin)[\'tasks\'];[print(f\'ID={t[\"id\"]} {t[\"type\"]} {t[\"model\"]} {t[\"status\"]} err={t.get(\"error\",\"\")[:50]}\') for t in tasks]"',
]

for cmd in cmds:
    print(f'>>> {cmd[:120]}')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()[:1000]
    err = stderr.read().decode()[:300]
    if out.strip():
        print(out)
    if err.strip():
        print(f'STDERR: {err}')
    print('---')

ssh.close()
