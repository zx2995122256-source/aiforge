#!/usr/bin/env python3
import paramiko, time

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."
PROJECT = "/home/ubuntu/oiioii"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)

def run(cmd, timeout=10):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        return out, err
    except:
        return "(timeout)", ""

print("Starting service (fire and forget)...")
run(f"echo 'zx4579561.' | sudo -S bash -c 'cd {PROJECT} && nohup python3 main.py > /tmp/oiioii.log 2>&1 &'", timeout=5)

time.sleep(6)

out, _ = run("echo 'zx4579561.' | sudo -S lsof -i :7861 2>/dev/null | head -3")
print(f"  Port 7861: {out[:150]}")

out, _ = run("tail -10 /tmp/oiioii.log 2>/dev/null")
print(f"  Log tail:\n  {out[:400]}")

ssh.close()
