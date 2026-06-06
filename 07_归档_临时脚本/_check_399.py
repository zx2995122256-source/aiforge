import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

stdin, stdout, stderr = ssh.exec_command('journalctl -u oiioii --no-pager --since "3 min ago" 2>/dev/null | grep -i "Task #399\\|resolve_video\\|videoUrl\\|upload_video_file\\|FOUND\\|empty_streak\\|init_workspace" | tail -20')
print(stdout.read().decode()[:2000])

ssh.close()
