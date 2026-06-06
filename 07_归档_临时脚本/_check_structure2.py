#!/usr/bin/env python3
import paramiko, time

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)

def run(cmd, timeout=15):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip()

print("=== Full structure ===")
print(run("find /home/ubuntu -maxdepth 3 -name '*.py' 2>/dev/null | grep -v __pycache__ | sort"))

print("\n=== api directory ===")
print(run("find /home/ubuntu -type d -name 'api' 2>/dev/null"))

print("\n=== Check aiforge dir ===")
print(run("ls -la /home/ubuntu/aiforge/ 2>/dev/null"))

ssh.close()
