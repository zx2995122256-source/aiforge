#!/usr/bin/env python3
import paramiko, time

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."
PROJECT = "/home/ubuntu/oiioii"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)

def run(cmd, timeout=20):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

print("1. Finding process on port 7861...")
out, _ = run("echo 'zx4579561.' | sudo -S lsof -i :7861 2>/dev/null | head -5")
print(f"  {out[:200]}")

print("\n2. Killing all main.py processes...")
out, _ = run("echo 'zx4579561.' | sudo -S pkill -9 -f 'python.*main.py' 2>&1; echo done")
print(f"  {out[:50]}")

time.sleep(2)

print("\n3. Confirming port is free...")
out, _ = run("echo 'zx4579561.' | sudo -S lsof -i :7861 2>/dev/null")
print(f"  Port 7861: {'FREE' if not out else 'STILL IN USE'}")

print("\n4. Starting service...")
out, _ = run(f"echo 'zx4579561.' | sudo -S bash -c 'cd {PROJECT} && nohup python3 main.py > /tmp/oiioii.log 2>&1 &' && echo STARTED", timeout=15)
print(f"  {out[:50]}")

time.sleep(5)

print("\n5. Checking...")
out, _ = run("echo 'zx4579561.' | sudo -S ps aux | grep 'main.py' | grep -v grep | head -3")
print(f"  Process: {'YES' if 'main.py' in out else 'NO'} {out[:100]}")

out, _ = run("echo 'zx4579561.' | sudo -S lsof -i :7861 2>/dev/null | head -3")
print(f"  Port 7861: {out[:100]}")

out, _ = run("tail -5 /tmp/oiioii.log 2>/dev/null")
print(f"  Log tail: {out[:300]}")

ssh.close()
print("\nDone!")
