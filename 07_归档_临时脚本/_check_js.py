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

# Check the generate store JS for reference_images parsing
out, _ = run('grep -o "reference_images[^,;]*" /home/ubuntu/aiforge/dist/assets/generate-*.js | head -10')
print('=== generate store JS ===')
print(out)

# Check the Workspace JS for retryTask function content
out, _ = run('cat /home/ubuntu/aiforge/dist/assets/Workspace-*.js')
print('\n=== Full Workspace JS ===')
print(out[:5000])

ssh.close()
