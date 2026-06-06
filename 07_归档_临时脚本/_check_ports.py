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

# Check if cloudflared is installed
out, _ = run('which cloudflared 2>/dev/null || echo NOT_FOUND')
print('=== cloudflared ===')
print(out)

# Check if cpolar is installed
out, _ = run('which cpolar 2>/dev/null || echo NOT_FOUND')
print('\n=== cpolar ===')
print(out)

# Check what's listening
out, _ = run('sudo ss -tlnp | grep LISTEN')
print('\n=== All listening ports ===')
print(out)

# Check if nginx is installed
out, _ = run('which nginx 2>/dev/null || echo NOT_FOUND')
print('\n=== nginx ===')
print(out)

# Check if there's any existing tunnel process
out, _ = run('ps aux | grep -E "cloudflared|cpolar|frp|ngrok" | grep -v grep')
print('\n=== Tunnel processes ===')
print(out or 'NONE')

# Check if port 80 or 443 is being used
out, _ = run('sudo ss -tlnp | grep -E ":80 |:443 "')
print('\n=== Port 80/443 ===')
print(out or 'NOT IN USE')

# Check Tencent Cloud security group - check if we can access from the server itself
out, _ = run('curl -s --connect-timeout 5 http://122.51.205.94:7862/api/pay/notify 2>&1 || echo FAILED')
print('\n=== Self-test port 7862 ===')
print(out)

ssh.close()
