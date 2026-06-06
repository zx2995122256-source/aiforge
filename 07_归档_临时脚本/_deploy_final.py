#!/usr/bin/env python3
import paramiko, os, time

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("Connecting...")
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)
print("Connected!")

sftp = ssh.open_sftp()

files = [
    (r"C:\Users\Administrator\Documents\OiioiiPool\config.py", "/opt/OiioiiPool/config.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\client.py", "/opt/OiioiiPool/core/client.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\engine.py", "/opt/OiioiiPool/core/engine.py"),
]

for local, remote in files:
    print(f"Uploading {os.path.basename(local)}...", end=" ", flush=True)
    sftp.put(local, remote)
    print("OK")

sftp.close()

print("\nVerifying...")
stdin, stdout, stderr = ssh.exec_command("grep 'timeout.*900' /opt/OiioiiPool/config.py | head -1")
print(f"  Gemini Omni timeout: {stdout.read().decode().strip()[:80]}")

stdin, stdout, stderr = ssh.exec_command("grep 'initial_delay' /opt/OiioiiPool/core/client.py | head -2")
print(f"  initial_delay: {stdout.read().decode().strip()[:80]}")

stdin, stdout, stderr = ssh.exec_command("grep 'RECOVERED' /opt/OiioiiPool/core/engine.py | head -1")
print(f"  Recovery logic: {stdout.read().decode().strip()[:80]}")

print("\nRestarting service...")
stdin, stdout, stderr = ssh.exec_command("cd /opt/OiioiiPool && sudo pkill -f 'python.*main.py' 2>/dev/null; sleep 2; sudo nohup python3 main.py > /dev/null 2>&1 & echo started")
print(f"  {stdout.read().decode().strip()}")

time.sleep(3)
stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'python.*main.py' | grep -v grep | head -1")
out = stdout.read().decode().strip()
print(f"  Running: {'YES' if 'python' in out else 'NO'} {out[:60]}")

ssh.close()
print("\nDeploy complete!")
