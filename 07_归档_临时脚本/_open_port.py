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

# Check firewall status
out, err = run('sudo ufw status')
print('=== UFW Status ===')
print(out or err)

# Check iptables
out, err = run('sudo iptables -L -n | head -30')
print('\n=== iptables (first 30 lines) ===')
print(out)

# Check if port 7861 is accessible (OiioiiPool)
out, err = run('sudo iptables -L -n | grep 7861')
print('\n=== iptables 7861 rules ===')
print(out or 'NO RULES')

# Check if port 7862 is accessible
out, err = run('sudo iptables -L -n | grep 7862')
print('\n=== iptables 7862 rules ===')
print(out or 'NO RULES')

# Check listening ports
out, err = run('sudo ss -tlnp | grep -E "786[12]"')
print('\n=== Listening ports ===')
print(out)

# Try to open port 7862
print('\n=== Opening port 7862 ===')
out, err = run('sudo ufw allow 7862/tcp')
print(out or err)

# Also check if ufw is active
out, err = run('sudo ufw status numbered | head -20')
print('\n=== UFW rules ===')
print(out)

ssh.close()
