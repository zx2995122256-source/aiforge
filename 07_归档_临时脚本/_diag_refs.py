import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

cmds = [
    # Check what reference_video value looks like in recent tasks
    'python3 -c "import sqlite3;conn=sqlite3.connect(\'/home/ubuntu/oiioii/data/oiioii_pool.db\');conn.row_factory=sqlite3.Row;cur=conn.execute(\'SELECT id,task_type,model_name,status,prompt,error_message FROM tasks ORDER BY id DESC LIMIT 10\');[print(dict(r)) for r in cur.fetchall()]"',
    # Check the engine.py to see how reference_video is passed
    'grep -n "reference_video\\|videoUrl\\|video_ref" /home/ubuntu/oiioii/core/client.py',
    # Check the server.py upload_video_ref endpoint
    'grep -n "upload_video_ref\\|video_ref\\|uri" /home/ubuntu/oiioii/api/server.py | head -20',
    # Check what the AiForge proxy does with video ref
    'cat /home/ubuntu/aiforge/backend/core/proxy.py | grep -n "upload_video_ref\\|video_ref\\|uri" | head -20',
    # Check the actual video ref URL format stored
    'python3 -c "import sqlite3;conn=sqlite3.connect(\'/home/ubuntu/oiioii/data/oiioii_pool.db\');cur=conn.execute(\'SELECT id, reference_video FROM tasks WHERE reference_video != \"\" AND reference_video IS NOT NULL ORDER BY id DESC LIMIT 5\');[print(r) for r in cur.fetchall()]" 2>/dev/null || echo "no reference_video column"',
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
