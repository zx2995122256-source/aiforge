import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

# Check task 399 and 396 status
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:7861/api/task/399')
print("Task 399:", stdout.read().decode()[:300])

stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:7861/api/task/396')
print("Task 396:", stdout.read().decode()[:300])

# Check the oiioii service log for these tasks
stdin, stdout, stderr = ssh.exec_command('journalctl -u oiioii --no-pager --since "15 min ago" 2>/dev/null | grep "Task #399\\|Task #396" | tail -10')
print("\nService logs:")
print(stdout.read().decode()[:1000])

ssh.close()
