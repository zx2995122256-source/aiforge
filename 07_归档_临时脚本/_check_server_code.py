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

# Check generate.py on server
out, _ = run('grep -n "reference_images\|reference_video\|ref_imgs\|ref_vid" /home/ubuntu/aiforge/backend/api/generate.py')
print('=== generate.py ref references ===')
print(out)

# Check db.py create_task on server
out, _ = run('grep -A5 "def create_task" /home/ubuntu/aiforge/backend/models/db.py')
print('\n=== db.py create_task ===')
print(out)

# Check the actual running process code
out, _ = run('cat /proc/534764/cmdline 2>/dev/null | tr "\\0" " "')
print(f'\n=== Running process ===')
print(out)

# Check if the service restarted with new code
out, _ = run('sudo systemctl status aiforge | head -8')
print(f'\n=== Service status ===')
print(out)

# Check the full generate.py to see the image and video endpoints
out, _ = run('grep -A20 "def generate_image" /home/ubuntu/aiforge/backend/api/generate.py | head -25')
print('\n=== generate_image endpoint ===')
print(out)

out, _ = run('grep -A20 "def generate_video" /home/ubuntu/aiforge/backend/api/generate.py | head -25')
print('\n=== generate_video endpoint ===')
print(out)

ssh.close()
