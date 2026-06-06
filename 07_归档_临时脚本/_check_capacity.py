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

print("=== Account pool status ===")
out = run("cd /home/ubuntu/oiioii && python3 -c \""
    "import sqlite3; conn=sqlite3.connect('data/oiioii_pool.db'); "
    "cur=conn.cursor(); "
    "cur.execute('SELECT status, video_used, COUNT(*), SUM(points_remaining) FROM accounts GROUP BY status, video_used'); "
    "for r in cur.fetchall(): print(r); "
    "cur.execute('SELECT COUNT(*) FROM accounts WHERE status=\\\"active\\\" AND video_used=0 AND points_remaining>=200'); "
    "print(f\\\"video_pool_available={cur.fetchone()[0]}\\\"); "
    "cur.execute('SELECT COUNT(*) FROM accounts WHERE status=\\\"active\\\" AND points_remaining>=30'); "
    "print(f\\\"image_pool_available={cur.fetchone()[0]}\\\"); "
    "cur.execute('SELECT COUNT(*) FROM accounts WHERE status=\\\"active\\\"'); "
    "print(f\\\"total_active={cur.fetchone()[0]}\\\"); "
    "\"")
print(out)

ssh.close()
