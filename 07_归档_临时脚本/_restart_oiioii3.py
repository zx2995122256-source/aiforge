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

# Kill ALL python3 processes related to oiioii/main
print('Killing all OiioiiPool processes...')
out, _ = run('sudo pkill -9 -f "python3.*main.py.*7861" 2>/dev/null; sudo pkill -9 -f "python3 main.py" 2>/dev/null; echo DONE')
print(out)
time.sleep(2)

# Also kill by port
run('sudo fuser -k 7861/tcp 2>/dev/null')
time.sleep(2)

# Verify clean
out, _ = run('sudo lsof -i :7861 2>/dev/null')
print(f'Port 7861: {"STILL IN USE - " + out if out else "FREE"}')

out, _ = run('ps aux | grep "python3 main" | grep -v grep')
print(f'Python main processes: {out or "NONE"}')

# Start fresh
print('\nStarting fresh OiioiiPool...')
run('cd /home/ubuntu/oiioii && nohup python3 main.py > /tmp/oiioii.log 2>&1 &')
time.sleep(5)

# Check
out, _ = run('sudo lsof -i :7861 2>/dev/null | head -3')
print(f'Port 7861: {out or "NOT LISTENING"}')

out, _ = run('curl -s http://localhost:7861/api/pool/status 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\'OK: accounts={d[\"total_accounts\"]} pts={d[\"total_points\"]}\')" 2>/dev/null || echo "API FAILED"')
print(f'API test: {out}')

out, _ = run('tail -10 /tmp/oiioii.log')
print(f'\nLog:\n{out}')

ssh.close()
