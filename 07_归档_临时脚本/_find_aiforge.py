#!/usr/bin/env python3
import paramiko

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)

def run(cmd, timeout=15):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip()

print("=== Finding projects ===")
print(run("ls /home/ubuntu/"))
print("\n=== Find main.py ===")
print(run("find / -maxdepth 4 -name 'main.py' 2>/dev/null | grep -v __pycache__ | head -10"))
print("\n=== Find payment.py ===")
print(run("find / -maxdepth 5 -name 'payment.py' 2>/dev/null | grep -v __pycache__ | head -5"))
print("\n=== Running python processes ===")
print(run("ps aux | grep python | grep -v grep | head -10"))
print("\n=== Ports ===")
print(run("echo 'zx4579561.' | sudo -S lsof -i :7861 -i :7862 2>/dev/null | head -10"))

ssh.close()
