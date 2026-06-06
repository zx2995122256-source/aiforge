#!/usr/bin/env python3
import paramiko, time

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)
print("Connected!")

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        return out, err
    except:
        return "(timeout)", ""

print("AiForge files are in /home/ubuntu/ directly")
print("Copying uploaded files...")

out, err = run("cp /home/ubuntu/payment.py /home/ubuntu/api/payment.py 2>/dev/null; ls /home/ubuntu/api/ 2>/dev/null | head -5")
print(f"  api dir: {out[:100]}")

if not out:
    print("  No api/ subdir, files are flat. Checking structure...")
    out, _ = run("ls /home/ubuntu/*.py | head -10")
    print(f"  Python files: {out}")

    out, _ = run("grep -r 'payment' /home/ubuntu/*.py 2>/dev/null | head -3")
    print(f"  Payment refs: {out[:100]}")

    out, _ = run("grep -r 'from api' /home/ubuntu/main.py 2>/dev/null | head -5")
    print(f"  Main imports: {out[:100]}")

ssh.close()
