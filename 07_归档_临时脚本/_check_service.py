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

print("Checking if service is already running...")
out, _ = run("ps aux | grep python | grep -v grep")
print(f"  Python processes:\n  {out[:300]}")

print("\nChecking who owns the process...")
out, _ = run("echo 'zx4579561.' | sudo -S ps aux | grep 'main.py' | grep -v grep | head -3")
print(f"  main.py processes: {out[:200]}")

print("\nTrying to start with sudo...")
out, err = run(f"echo 'zx4579561.' | sudo -S bash -c 'cd {PROJECT} && nohup python3 main.py > /tmp/oiioii.log 2>&1 &' && echo STARTED", timeout=15)
print(f"  Start: {out[:50]}")

time.sleep(4)
out, _ = run("ps aux | grep 'main.py' | grep -v grep | head -3")
print(f"  Running: {'YES' if 'main.py' in out else 'NO'} {out[:100]}")

if 'main.py' not in out:
    print("\nChecking log...")
    out, _ = run("cat /tmp/oiioii.log 2>/dev/null | tail -20")
    print(f"  Log: {out[:500]}")

ssh.close()
