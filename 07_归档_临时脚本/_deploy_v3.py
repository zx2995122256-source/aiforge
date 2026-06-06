#!/usr/bin/env python3
import paramiko, time

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."
PROJECT = "/home/ubuntu/oiioii"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)
print("Connected!")

sftp = ssh.open_sftp()

files = [
    (r"C:\Users\Administrator\Documents\OiioiiPool\config.py", "config.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\client.py", "client.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\engine.py", "engine.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\pool.py", "pool.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\db.py", "db.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\main.py", "main.py"),
]

for local, fname in files:
    print(f"Uploading {fname}...", end=" ", flush=True)
    sftp.put(local, f"/home/ubuntu/{fname}")
    print("OK")

sftp.close()

def run(cmd, timeout=20):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        return out, err
    except:
        return "(timeout)", ""

print("\nCopying to project dir...")
out, err = run(f"cp /home/ubuntu/config.py {PROJECT}/config.py && cp /home/ubuntu/client.py {PROJECT}/core/client.py && cp /home/ubuntu/engine.py {PROJECT}/core/engine.py && cp /home/ubuntu/pool.py {PROJECT}/core/pool.py && cp /home/ubuntu/db.py {PROJECT}/core/db.py && cp /home/ubuntu/main.py {PROJECT}/main.py && echo COPIED")
print(f"  {'OK' if 'COPIED' in out else 'FAILED ' + err[:100]}")

print("\nVerifying...")
out, _ = run(f"grep 'MAX_CONCURRENT_GEN = 20' {PROJECT}/config.py")
print(f"  MAX_CONCURRENT_GEN=20: {'YES' if out else 'NO'}")
out, _ = run(f"grep 'uploaded_refs' {PROJECT}/core/engine.py | head -1")
print(f"  uploaded_refs fix: {'YES' if out else 'NO'}")
out, _ = run(f"grep 'daily_claim' {PROJECT}/core/client.py | head -1")
print(f"  daily_claim: {'YES' if out else 'NO'}")

print("\nRestarting...")
run("echo 'zx4579561.' | sudo -S kill -9 $(echo 'zx4579561.' | sudo -S lsof -t -i :7861) 2>/dev/null; echo killed")
time.sleep(2)
run(f"echo 'zx4579561.' | sudo -S bash -c 'cd {PROJECT} && nohup python3 main.py > /tmp/oiioii.log 2>&1 &'", timeout=5)
time.sleep(5)

out, _ = run("echo 'zx4579561.' | sudo -S lsof -i :7861 2>/dev/null | head -2")
print(f"  Port 7861: {'RUNNING' if 'python' in out else 'NOT RUNNING'}")

out, _ = run("tail -5 /tmp/oiioii.log 2>/dev/null")
print(f"  Log: {out[:200]}")

ssh.close()
print("\nDeploy complete!")
