#!/usr/bin/env python3
import paramiko

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)

cmds = [
    "ls /opt/ 2>/dev/null",
    "ls /home/ubuntu/ 2>/dev/null",
    "ls /root/ 2>/dev/null",
    "echo 'zx4579561.' | sudo -S ls /opt/ 2>/dev/null",
    "echo 'zx4579561.' | sudo -S find /opt /home /root -maxdepth 3 -name 'main.py' 2>/dev/null | head -5",
    "echo 'zx4579561.' | sudo -S find /opt /home /root -maxdepth 3 -name 'oiioii_pool.db' 2>/dev/null | head -5",
    "echo 'zx4579561.' | sudo -S ps aux | grep python | grep -v grep | head -5",
]

for cmd in cmds:
    print(f"\n> {cmd[:80]}")
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=20)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print(f"  {out[:300]}")
        if err and 'password' not in err.lower():
            print(f"  ERR: {err[:200]}")
    except Exception as e:
        print(f"  Error: {e}")

ssh.close()
