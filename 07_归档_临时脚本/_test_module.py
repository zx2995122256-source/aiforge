#!/usr/bin/env python3
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', password='zx4579561.', timeout=15)

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

# Clear pyc cache and restart
print("Clearing __pycache__...")
out, _ = run('find /home/ubuntu/aiforge/backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; echo DONE')
print(out)

# Restart service
print("Restarting AiForge...")
run('sudo systemctl restart aiforge')
time.sleep(4)

# Check service
out, _ = run('sudo systemctl status aiforge | head -5')
print(f'Service: {out}')

# Now test by creating a task with reference_images directly
script = """import requests, json

# First find a valid user
import sqlite3
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cur = conn.cursor()
user = cur.execute('SELECT id, email FROM users LIMIT 1').fetchone()
conn.close()
if not user:
    print('No users found')
    exit()
uid, email = user
print(f'Using user: #{uid} {email}')

# Check what the generate endpoint actually does - look at the source
import importlib.util
spec = importlib.util.spec_from_file_location('generate', '/home/ubuntu/aiforge/backend/api/generate.py')
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    print('Module loaded OK')
    # Check if ImageReq has reference_images
    import inspect
    src = inspect.getsource(mod.ImageReq)
    print(f'ImageReq fields: {src[:200]}')
except Exception as e:
    print(f'Module load error: {e}')
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_test_module.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_test_module.py')
print(f'\n=== Module test ===')
print(out)
if err:
    print(f'ERR: {err[:300]}')

# Also directly test the create_task function
script2 = """import sqlite3, json, sys
sys.path.insert(0, '/home/ubuntu/aiforge/backend')
from models.db import create_task, _get_conn

# Create a test task with reference data
tid = create_task(1, 'image', 'GPT-Image2', 'test prompt', 10, 999, 
                  reference_images='["http://example.com/img1.png"]', 
                  reference_video='http://example.com/vid1.mp4')
print(f'Created test task #{tid}')

# Read it back
conn = _get_conn()
row = conn.execute('SELECT reference_images, reference_video FROM tasks WHERE id=?', (tid,)).fetchone()
print(f'ref_imgs={row[0]}')
print(f'ref_vid={row[1]}')
conn.close()

# Clean up
conn = _get_conn()
conn.execute('DELETE FROM tasks WHERE id=?', (tid,))
conn.commit()
conn.close()
print('Cleaned up')
"""

with sftp.open('/tmp/_test_create.py', 'w') as f:
    f.write(script2)
sftp.close()

out2, err2 = run('python3 /tmp/_test_create.py')
print(f'\n=== create_task test ===')
print(out2)
if err2:
    print(f'ERR: {err2[:300]}')

ssh.close()
