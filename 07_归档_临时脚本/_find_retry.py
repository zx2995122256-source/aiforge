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

# Find the retry function - search for refImages assignment near currentTab
script = """import re
js = open('/home/ubuntu/aiforge/dist/assets/Workspace-CQ9o0z3E.js').read()

# Find all occurrences of refImages assignment
for m in re.finditer(r'refImages\s*=\s*[^;]{5,80}', js):
    start = max(0, m.start()-50)
    end = min(len(js), m.end()+50)
    print(f'--- pos {m.start()} ---')
    print(js[start:end])
    print()
"""
sftp = ssh.open_sftp()
with sftp.open('/tmp/_find_retry.py', 'w') as f:
    f.write(script)
sftp.close()

out, _ = run('python3 /tmp/_find_retry.py')
print(out[:3000])

ssh.close()
