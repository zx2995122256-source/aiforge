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

# Get the full retry function context
script = """js = open('/home/ubuntu/aiforge/dist/assets/Workspace-CQ9o0z3E.js').read()
idx = js.find('.reference_images&&o.reference_images.length>0')
if idx >= 0:
    # Go back to find the function start
    start = max(0, idx - 300)
    end = min(len(js), idx + 600)
    print(js[start:end])
else:
    print('NOT FOUND')
"""
sftp = ssh.open_sftp()
with sftp.open('/tmp/_find_retry2.py', 'w') as f:
    f.write(script)
sftp.close()

out, _ = run('python3 /tmp/_find_retry2.py')
print(out)

ssh.close()
