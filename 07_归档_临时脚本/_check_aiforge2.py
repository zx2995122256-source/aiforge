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

# Check current payment.py on server
out, _ = run('head -30 /home/ubuntu/aiforge/backend/api/payment.py')
print('=== Server payment.py head ===')
print(out)

# Check if free-sign notify exists
out, _ = run('grep -c "free_sign_notify" /home/ubuntu/aiforge/backend/api/payment.py')
print('\n=== Has free_sign_notify? ===')
print(out)

# Check if admin confirm exists
out, _ = run('grep -c "confirm_order" /home/ubuntu/aiforge/backend/admin.py')
print('\n=== Has confirm_order in admin? ===')
print(out)

# Check AiForge config for payment settings
out, _ = run('cat /home/ubuntu/aiforge/backend/config.py')
print('\n=== AiForge config.py ===')
print(out[:3000])

# Check AiForge main.py
out, _ = run('cat /home/ubuntu/aiforge/backend/main.py')
print('\n=== AiForge main.py ===')
print(out[:2000])

# Check if AIFORGE_NOTIFY_KEY env var is set
out, _ = run('cat /proc/330113/environ 2>/dev/null | tr "\\0" "\\n" | grep AIFORGE')
print('\n=== AIFORGE env vars ===')
print(out or 'NONE')

# Check the systemd or startup script
out, _ = run('cat /etc/systemd/system/aiforge*.service 2>/dev/null || echo NO_SYSTEMD')
print('\n=== systemd service ===')
print(out)

# Check how AiForge is started
out, _ = run('cat /proc/330113/cmdline 2>/dev/null | tr "\\0" " "')
print('\n=== AiForge cmdline ===')
print(out)

out, _ = run('ls -la /home/ubuntu/aiforge/backend/api/')
print('\n=== AiForge api dir ===')
print(out)

ssh.close()
