#!/usr/bin/env python3
import paramiko, os

KEY_PATH = r"C:\Users\Administrator\Documents\ssh_key.pem"
SERVER = "122.51.205.94"
REMOTE_DIR = "/opt/OiioiiPool"

files_to_deploy = [
    ("OiioiiPool/config.py", "config.py"),
    ("OiioiiPool/core/client.py", "core/client.py"),
    ("OiioiiPool/core/engine.py", "core/engine.py"),
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username="root", key_filename=KEY_PATH)

sftp = ssh.open_sftp()

for local_rel, remote_rel in files_to_deploy:
    local = os.path.join(r"C:\Users\Administrator\Documents", local_rel)
    remote = f"{REMOTE_DIR}/{remote_rel}"
    print(f"Uploading {local_rel} -> {remote}")
    sftp.put(local, remote)

sftp.close()

print("\nRestarting service...")
stdin, stdout, stderr = ssh.exec_command("cd /opt/OiioiiPool && supervisorctl restart oiioii_pool 2>/dev/null || systemctl restart oiioii_pool 2>/dev/null || (pkill -f 'python.*main.py' && sleep 2 && nohup python3 main.py > /dev/null 2>&1 &) && echo 'Restarted'")
print(stdout.read().decode()[:500])
print(stderr.read().decode()[:500])

ssh.close()
print("\nDeploy complete!")
