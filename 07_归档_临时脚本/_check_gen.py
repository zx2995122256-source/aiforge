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

# Check the actual generate.py lines around create_task
out, _ = run('sed -n "100,140p" /home/ubuntu/aiforge/backend/api/generate.py')
print('=== generate.py lines 100-140 ===')
print(out)

# Check if the service is using the updated code - look at the process start time
out, _ = run('ps -p $(pgrep -f "uvicorn.*7862") -o lstart=')
print(f'\n=== Process start time ===')
print(out)

# Check the AiForge service log for any errors
out, _ = run('sudo journalctl -u aiforge --since "5 min ago" --no-pager | tail -20')
print(f'\n=== Recent service log ===')
print(out)

ssh.close()
