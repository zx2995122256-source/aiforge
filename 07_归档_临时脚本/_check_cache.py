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

# Check the current index.html
out, _ = run('cat /home/ubuntu/aiforge/dist/index.html')
print('=== index.html ===')
print(out)

# Check nginx cache headers
out, _ = run('curl -sI http://localhost:7862/ | head -15')
print('\n=== Response headers for / ===')
print(out)

# Check the JS file hash
out, _ = run('ls -la /home/ubuntu/aiforge/dist/assets/Workspace-*.js')
print('\n=== Workspace JS files ===')
print(out)

ssh.close()
