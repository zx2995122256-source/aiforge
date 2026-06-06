import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

stdin, stdout, stderr = ssh.exec_command('cat /tmp/test_all_refs.log')
print(stdout.read().decode()[:3000])

print('\n--- SERVICE LOGS ---')
stdin, stdout, stderr = ssh.exec_command('journalctl -u oiioii --no-pager --since "3 min ago" 2>/dev/null | grep -iE "FOUND|has_list|resolve_video|empty_streak|Task #40" | tail -15')
print(stdout.read().decode()[:1000])

ssh.close()
