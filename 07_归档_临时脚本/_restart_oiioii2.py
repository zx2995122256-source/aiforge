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

# Kill ALL python processes on port 7861
print('Force killing all processes on port 7861...')
out, _ = run('sudo fuser -k 7861/tcp 2>/dev/null')
print(f'  fuser output: {out}')
time.sleep(3)

# Verify port is free
out, _ = run('sudo lsof -i :7861 2>/dev/null')
print(f'Port 7861: {"STILL IN USE" if out else "FREE"}')

# Start new process
print('Starting new OiioiiPool...')
run('cd /home/ubuntu/oiioii && nohup python3 main.py > /tmp/oiioii.log 2>&1 &')
time.sleep(5)

# Verify
out, _ = run('sudo lsof -i :7861 2>/dev/null | head -3')
print(f'Port 7861: {"LISTENING" if "python" in out else "NOT LISTENING"}')
print(out)

# Quick API test
out, _ = run('curl -s http://localhost:7861/api/pool/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\'OK: accounts={d[\"total_accounts\"]} active={d[\"active_accounts\"]} pts={d[\"total_points\"]}\')" 2>/dev/null || echo FAILED')
print(f'API: {out}')

# Check log for errors
out, _ = run('tail -5 /tmp/oiioii.log')
print(f'Log tail: {out}')

ssh.close()
print('\nDone!')
