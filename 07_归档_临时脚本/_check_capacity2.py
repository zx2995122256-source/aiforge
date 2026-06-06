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
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

print("=== DB query ===")
out, err = run("cd /home/ubuntu/oiioii && python3 -c 'import sqlite3; conn=sqlite3.connect(\"data/oiioii_pool.db\"); cur=conn.cursor(); cur.execute(\"SELECT status, video_used, COUNT(*), SUM(points_remaining) FROM accounts GROUP BY status, video_used\"); [print(r) for r in cur.fetchall()]'")
print(f"out: {out}")
if err:
    print(f"err: {err[:200]}")

print("\n=== Simple count ===")
out, err = run("cd /home/ubuntu/oiioii && python3 -c 'import sqlite3; c=sqlite3.connect(\"data/oiioii_pool.db\"); r=c.execute(\"SELECT COUNT(*) FROM accounts\").fetchone(); print(r[0])'")
print(f"Total accounts: {out}")

out, err = run("cd /home/ubuntu/oiioii && python3 -c 'import sqlite3; c=sqlite3.connect(\"data/oiioii_pool.db\"); r=c.execute(\"SELECT COUNT(*) FROM accounts WHERE status=\\\"active\\\"\").fetchone(); print(r[0])'")
print(f"Active accounts: {out}")

out, err = run("cd /home/ubuntu/oiioii && python3 -c 'import sqlite3; c=sqlite3.connect(\"data/oiioii_pool.db\"); r=c.execute(\"SELECT COUNT(*) FROM accounts WHERE status=\\\"active\\\" AND video_used=0 AND points_remaining>=200\").fetchone(); print(r[0])'")
print(f"Video pool (200+pts, video_used=0): {out}")

out, err = run("cd /home/ubuntu/oiioii && python3 -c 'import sqlite3; c=sqlite3.connect(\"data/oiioii_pool.db\"); r=c.execute(\"SELECT COUNT(*) FROM accounts WHERE status=\\\"active\\\" AND points_remaining>=30\").fetchone(); print(r[0])'")
print(f"Image pool (30+pts): {out}")

out, err = run("cd /home/ubuntu/oiioii && python3 -c 'import sqlite3; c=sqlite3.connect(\"data/oiioii_pool.db\"); r=c.execute(\"SELECT SUM(points_remaining) FROM accounts WHERE status=\\\"active\\\"\").fetchone(); print(r[0])'")
print(f"Total points: {out}")

ssh.close()
