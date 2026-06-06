import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

cmds = [
    # Compare accounts used for successful vs stuck tasks
    'python3 -c "import sqlite3;conn=sqlite3.connect(\'/home/ubuntu/oiioii/data/oiioii_pool.db\');cur=conn.execute(\'SELECT t.id,t.account_id,a.email,a.points_remaining,t.status,t.result_uri FROM tasks t JOIN accounts a ON t.account_id=a.id WHERE t.id IN (390,392,396)\');[print(r) for r in cur.fetchall()]"',
    # Check the full engine log for task 396 submission
    'journalctl -u oiioii --no-pager 2>/dev/null | grep "Task #396\\|Task #390" | head -20',
    # Check how many accounts have video_used=0 (fresh video pool)
    'python3 -c "import sqlite3;conn=sqlite3.connect(\'/home/ubuntu/oiioii/data/oiioii_pool.db\');cur=conn.execute(\'SELECT video_used, COUNT(*) FROM accounts WHERE status=\\\"active\\\" GROUP BY video_used\');[print(r) for r in cur.fetchall()]"',
]

for cmd in cmds:
    print(f'>>> {cmd[:120]}')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()[:1500]
    if out.strip():
        print(out)
    print('---')

ssh.close()
