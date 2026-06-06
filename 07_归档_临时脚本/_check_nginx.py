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

# Check nginx config
out, _ = run('cat /etc/nginx/nginx.conf')
print('=== nginx.conf ===')
print(out[:3000])

# Check sites-enabled
out, _ = run('ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo NO_SITES')
print('\n=== sites-enabled ===')
print(out)

# Check default site config
out, _ = run('cat /etc/nginx/sites-enabled/default 2>/dev/null || echo NO_DEFAULT')
print('\n=== default site ===')
print(out[:3000])

# Check conf.d
out, _ = run('ls -la /etc/nginx/conf.d/ 2>/dev/null')
print('\n=== conf.d ===')
print(out)

out, _ = run('cat /etc/nginx/conf.d/*.conf 2>/dev/null || echo NO_CONF_D')
print('\n=== conf.d configs ===')
print(out[:3000])

# Test if port 80 is accessible from outside
out, _ = run('curl -s --connect-timeout 5 http://127.0.0.1/ | head -5')
print('\n=== localhost:80 response ===')
print(out)

ssh.close()
