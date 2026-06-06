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

print("Force killing PID 490392...")
out, _ = run("echo 'zx4579561.' | sudo -S kill -9 490392 2>&1; echo done")
print(f"  {out}")

time.sleep(2)

out, _ = run("echo 'zx4579561.' | sudo -S lsof -i :7861 2>/dev/null")
print(f"  Port 7861: {'FREE' if not out else 'STILL IN USE: ' + out[:100]}")

if not out:
    print("\nStarting service...")
    out, _ = run(f"echo 'zx4579561.' | sudo -S bash -c 'cd {PROJECT} && nohup python3 main.py > /tmp/oiioii.log 2>&1 &' && echo STARTED", timeout=15)
    print(f"  {out}")

    time.sleep(5)

    out, _ = run("echo 'zx4579561.' | sudo -S lsof -i :7861 2>/dev/null | head -3")
    print(f"  Port 7861: {out[:100]}")

    out, _ = run("tail -8 /tmp/oiioii.log 2>/dev/null")
    print(f"  Log: {out[:400]}")

ssh.close()
