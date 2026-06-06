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
    (r"C:\Users\Administrator\Documents\OiioiiPool\config.py", "config.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\client.py", "client.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\engine.py", "engine.py"),
]

for local, fname in files:
    remote_tmp = f"/home/ubuntu/{fname}"
    print(f"Uploading {os.path.basename(local)}...", end=" ", flush=True)
    sftp.put(local, remote_tmp)
    print("OK")

sftp.close()

print("\nMoving files with sudo...")
cmd = "echo 'zx4579561.' | sudo -S cp /home/ubuntu/config.py /opt/OiioiiPool/config.py && echo 'zx4579561.' | sudo -S cp /home/ubuntu/client.py /opt/OiioiiPool/core/client.py && echo 'zx4579561.' | sudo -S cp /home/ubuntu/engine.py /opt/OiioiiPool/core/engine.py && echo COPY_OK"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
out = stdout.read().decode()
err = stderr.read().decode()
print(f"  Copy: {'OK' if 'COPY_OK' in out else 'FAILED'}")
if 'COPY_OK' not in out:
    print(f"  Error: {err[:200]}")

print("\nVerifying...")
stdin, stdout, stderr = ssh.exec_command("grep 'timeout.*900' /opt/OiioiiPool/config.py | head -1")
print(f"  Gemini Omni timeout: {stdout.read().decode().strip()[:80]}")

stdin, stdout, stderr = ssh.exec_command("grep 'initial_delay' /opt/OiioiiPool/core/client.py | head -2")
print(f"  initial_delay: {stdout.read().decode().strip()[:80]}")

stdin, stdout, stderr = ssh.exec_command("grep 'RECOVERED' /opt/OiioiiPool/core/engine.py | head -1")
print(f"  Recovery logic: {stdout.read().decode().strip()[:80]}")

print("\nRestarting service...")
cmd = "echo 'zx4579561.' | sudo -S pkill -f 'python.*main.py' 2>/dev/null; sleep 2; echo 'zx4579561.' | sudo -S bash -c 'cd /opt/OiioiiPool && nohup python3 main.py > /dev/null 2>&1 &' && echo RESTART_OK"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
out = stdout.read().decode()
print(f"  Restart: {'OK' if 'RESTART_OK' in out else 'checking...'}")

time.sleep(3)
stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'python.*main.py' | grep -v grep | head -1")
out = stdout.read().decode().strip()
print(f"  Running: {'YES' if 'python' in out else 'NO'} {out[:60]}")

ssh.close()
print("\nDeploy complete!")
