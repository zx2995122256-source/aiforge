#!/usr/bin/env python3
import paramiko

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)

def run(cmd, timeout=10):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip()

print("=== CPU ===")
print(run("lscpu | grep -E 'Model name|CPU\\(s\\)|Thread|Core|Socket'"))

print("\n=== Memory ===")
print(run("free -h"))

print("\n=== Disk ===")
print(run("df -h /"))

print("\n=== GPU ===")
print(run("lspci | grep -i vga 2>/dev/null || echo 'No GPU info'"))

print("\n=== OS ===")
print(run("cat /etc/os-release | head -4"))

print("\n=== Network ===")
print(run("curl -s ifconfig.me 2>/dev/null || echo 'No external IP'"))

ssh.close()
