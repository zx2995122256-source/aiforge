#!/usr/bin/env python3
import paramiko

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)

cmds = [
    "find / -name 'main.py' -path '*/Oiioii*' 2>/dev/null | head -5",
    "find / -name 'engine.py' -path '*/Oiioii*' 2>/dev/null | head -5",
    "find / -name 'client.py' -path '*/Oiioii*' 2>/dev/null | head -5",
    "ls -la /opt/ 2>/dev/null | head -10",
    "ls -la /home/ubuntu/ 2>/dev/null | head -10",
    "ps aux | grep python | grep -v grep | head -5",
    "find / -name 'oiioii_pool.db' 2>/dev/null | head -5",
]

for cmd in cmds:
    print(f"\n> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode().strip()
    print(f"  {out[:300] if out else '(empty)'}")

ssh.close()
