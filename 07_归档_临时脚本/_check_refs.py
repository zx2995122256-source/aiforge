#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', password='zx4579561.', timeout=15)

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

# Check if the DB has the new columns
script = """import sqlite3
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cur = conn.cursor()
schema = cur.execute("PRAGMA table_info(tasks)").fetchall()
for col in schema:
    print(f'  {col[1]} ({col[2]}) default={col[4]}')
print()

# Check recent tasks with reference data
rows = cur.execute('SELECT id, task_type, status, reference_images, reference_video FROM tasks ORDER BY id DESC LIMIT 10').fetchall()
for r in rows:
    print(f'#{r[0]} type={r[1]} status={r[2]}')
    print(f'  ref_imgs={r[3][:100] if r[3] else "NULL/EMPTY"}')
    print(f'  ref_vid={r[4][:100] if r[4] else "NULL/EMPTY"}')
conn.close()
"""
sftp = ssh.open_sftp()
with sftp.open('/tmp/_check_refs.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_check_refs.py')
print('=== DB columns & reference data ===')
print(out)
if err:
    print(f'ERR: {err[:300]}')

# Also check what the API returns for tasks
out, _ = run('curl -s http://localhost:7862/api/generate/tasks -H "Authorization: Bearer $(curl -s http://localhost:7862/api/auth/login -H \'Content-Type: application/json\' -d \'{"email":"test@test.com","password":"test123"}\' | python3 -c \'import sys,json;print(json.load(sys.stdin).get("token",""))\')" 2>/dev/null | python3 -c "import sys,json;tasks=json.load(sys.stdin).get(\'tasks\',[]);[print(f\'#{t.get(\"id\")} refs_imgs={str(t.get(\"reference_images\",\"\"))[:80]} ref_vid={str(t.get(\"reference_video\",\"\"))[:80]}\') for t in tasks[-5:]]" 2>/dev/null || echo "API test failed"')
print('\n=== API task response ===')
print(out)

ssh.close()
