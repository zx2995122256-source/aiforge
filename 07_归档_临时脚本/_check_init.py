import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

# Check if _init_workspace_assets worked
stdin, stdout, stderr = ssh.exec_command('journalctl -u oiioii --no-pager --since "10 min ago" 2>/dev/null | grep -i "init_workspace" | tail -5')
print("init_workspace logs:")
print(stdout.read().decode()[:500])

# Check task 399 current status
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:7861/api/task/399')
print("\nTask 399:")
print(stdout.read().decode()[:300])

# Check latest poll status
stdin, stdout, stderr = ssh.exec_command('journalctl -u oiioii --no-pager --since "1 min ago" 2>/dev/null | grep "Task #399\\|poll #" | tail -5')
print("\nLatest poll:")
print(stdout.read().decode()[:500])

ssh.close()
