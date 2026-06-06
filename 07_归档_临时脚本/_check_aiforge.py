#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', password='zx4579561.', timeout=15)

def run(cmd, timeout=10):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

out, _ = run('ps aux | grep python | grep -v grep')
print('=== Python processes ===')
print(out or 'NONE')

out, _ = run('sudo lsof -i :7862 2>/dev/null | head -3')
print('\n=== Port 7862 ===')
print(out or 'NOT LISTENING')

out, _ = run('find /home/ubuntu -maxdepth 3 -name main.py 2>/dev/null | head -5')
print('\n=== main.py locations ===')
print(out or 'NONE')

out, _ = run('ls -la /home/ubuntu/*.py 2>/dev/null | head -10')
print('\n=== .py files in home ===')
print(out or 'NONE')

out, _ = run('find /home/ubuntu -maxdepth 3 -type d -name api 2>/dev/null | head -5')
print('\n=== api directories ===')
print(out or 'NONE')

out, _ = run('find /home/ubuntu -maxdepth 4 -name payment.py 2>/dev/null | head -5')
print('\n=== payment.py locations ===')
print(out or 'NONE')

out, _ = run('find /home/ubuntu -maxdepth 3 -name config.py 2>/dev/null | head -5')
print('\n=== config.py locations ===')
print(out or 'NONE')

out, _ = run('ls -la /home/ubuntu/api/ 2>/dev/null | head -10')
print('\n=== /home/ubuntu/api/ contents ===')
print(out or 'NOT EXISTS')

out, _ = run('cat /home/ubuntu/main.py 2>/dev/null | head -20')
print('\n=== /home/ubuntu/main.py head ===')
print(out or 'NOT EXISTS')

ssh.close()
