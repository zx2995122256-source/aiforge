import paramiko, time

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

stdin, stdout, stderr = ssh.exec_command('cat /tmp/test_refs_server.log')
log = stdout.read().decode()
print(log if log else "(no output yet)")

ssh.close()
