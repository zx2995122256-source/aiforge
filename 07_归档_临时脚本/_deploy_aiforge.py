#!/usr/bin/env python3
import paramiko, time

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)
print("Connected!")

sftp = ssh.open_sftp()

files = [
    (r"C:\Users\Administrator\Documents\AiForge\backend\api\payment.py", "payment.py"),
    (r"C:\Users\Administrator\Documents\AiForge\backend\admin.py", "admin.py"),
]

for local, fname in files:
    print(f"Uploading {fname}...", end=" ", flush=True)
    sftp.put(local, f"/home/ubuntu/{fname}")
    print("OK")

sftp.close()

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        return out, err
    except:
        return "(timeout)", ""

print("\nFinding AiForge project...")
out, _ = run("find /home/ubuntu -maxdepth 3 -name 'main.py' -path '*/AiForge*' 2>/dev/null | head -3")
print(f"  AiForge main.py: {out}")

out, _ = run("find /home/ubuntu -maxdepth 3 -name 'payment.py' -path '*/api*' 2>/dev/null | head -3")
print(f"  Existing payment.py: {out}")

aiforge_dir = ""
if out:
    aiforge_dir = "/".join(out.split("/")[:-2])
    print(f"  AiForge dir: {aiforge_dir}")

if aiforge_dir:
    print(f"\nCopying files...")
    out, err = run(f"cp /home/ubuntu/payment.py {aiforge_dir}/api/payment.py && cp /home/ubuntu/admin.py {aiforge_dir}/admin.py && echo COPIED")
    print(f"  {'OK' if 'COPIED' in out else 'FAILED ' + err[:100]}")

    print("\nRestarting AiForge...")
    out, _ = run(f"echo 'zx4579561.' | sudo -S lsof -i :7862 -t 2>/dev/null")
    if out:
        run(f"echo 'zx4579561.' | sudo -S kill -9 {out.split()[0]} 2>/dev/null")
        time.sleep(2)

    run(f"echo 'zx4579561.' | sudo -S bash -c 'cd {aiforge_dir} && nohup python3 main.py > /tmp/aiforge.log 2>&1 &'", timeout=5)
    time.sleep(5)

    out, _ = run("echo 'zx4579561.' | sudo -S lsof -i :7862 2>/dev/null | head -2")
    print(f"  Port 7862: {'RUNNING' if 'python' in out else 'NOT RUNNING'}")
else:
    print("  Could not find AiForge directory!")

ssh.close()
print("\nDone!")
