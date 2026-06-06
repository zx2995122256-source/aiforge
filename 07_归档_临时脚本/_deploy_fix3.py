import paramiko, time

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

with open(r'C:\Users\Administrator\Documents\OiioiiPool\core\client.py', 'r', encoding='utf-8') as f:
    client_code = f.read()

sftp = ssh.open_sftp()
with sftp.open('/home/ubuntu/oiioii/core/client.py', 'w') as f:
    f.write(client_code)
print("Uploaded client.py")

stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart oiioii')
print("Restarting...")
time.sleep(5)

stdin, stdout, stderr = ssh.exec_command('systemctl is-active oiioii')
print(f"Service: {stdout.read().decode().strip()}")

ssh.close()
