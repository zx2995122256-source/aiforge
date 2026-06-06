import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

stdin, stdout, stderr = ssh.exec_command('cat /tmp/test_videoref_fix.log')
log = stdout.read().decode()
print(log if log else "(no output yet)")

# Also check the oiioii service log for _resolve_video_ref
stdin, stdout, stderr = ssh.exec_command('journalctl -u oiioii --no-pager --since "3 min ago" 2>/dev/null | grep -i "resolve_video\\|videoUrl\\|upload_video\\|video_ref\\|manualRefresh\\|_upload_to\\|WARNING" | tail -20')
log2 = stdout.read().decode()
print("\n--- Service logs ---")
print(log2 if log2 else "(no matching logs)")

ssh.close()
