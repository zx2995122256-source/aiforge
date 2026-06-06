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

# Check OiioiiPool full log
out, _ = run('wc -l /tmp/oiioii.log')
print(f'Log lines: {out}')

# Get the last 50 lines with all content
out, _ = run('tail -50 /tmp/oiioii.log')
print('\n=== Last 50 lines ===')
print(out[:3000])

# Check if there's a different log file
out, _ = run('find /home/ubuntu/oiioii -name "*.log" 2>/dev/null')
print(f'\n=== Log files ===')
print(out)

# Check the OiioiiPool process stdout/stderr
out, _ = run('sudo cat /proc/528215/fd/1 2>/dev/null | tail -30 || echo "cant read fd"')
print(f'\n=== Process stdout ===')
print(out[:1000])

# Check how OiioiiPool was started
out, _ = run('cat /proc/528215/cmdline 2>/dev/null | tr "\\0" " "')
print(f'\n=== Process cmdline ===')
print(out)

# Check the systemd journal for oiioii
out, _ = run('sudo journalctl -u oiioii --since "10 min ago" --no-pager 2>/dev/null | tail -20 || echo "no systemd service"')
print(f'\n=== systemd oiioii ===')
print(out)

ssh.close()
