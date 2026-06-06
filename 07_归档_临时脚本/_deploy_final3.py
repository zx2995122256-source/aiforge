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

def run(cmd, timeout=20):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

print("\n1. Backing up old files...")
for f in ["config.py", "core/client.py", "core/engine.py"]:
    out, err = run(f"cp {PROJECT}/{f} {PROJECT}/{f}.bak 2>&1")
    print(f"  {f}: backed up")

print("\n2. Deploying new files...")
files = {
    "/home/ubuntu/config.py": f"{PROJECT}/config.py",
    "/home/ubuntu/client.py": f"{PROJECT}/core/client.py",
    "/home/ubuntu/engine.py": f"{PROJECT}/core/engine.py",
}
for src, dst in files.items():
    out, err = run(f"cp {src} {dst} 2>&1")
    print(f"  {src.split('/')[-1]} -> {dst}: {'OK' if not err or 'cannot' not in err else err[:100]}")

print("\n3. Verifying...")
out, _ = run(f"grep 'timeout.*900' {PROJECT}/config.py | head -1")
print(f"  Gemini Omni timeout: {out[:80]}")

out, _ = run(f"grep 'initial_delay' {PROJECT}/core/client.py | head -2")
print(f"  initial_delay: {out[:80]}")

out, _ = run(f"grep 'RECOVERED' {PROJECT}/core/engine.py | head -1")
print(f"  Recovery logic: {out[:80]}")

print("\n4. Restarting service...")
out, err = run(f"cd {PROJECT} && pkill -f 'python.*main.py' 2>/dev/null; sleep 2; nohup python3 main.py > /dev/null 2>&1 & echo started", timeout=15)
print(f"  Restart: {out[:50]}")

time.sleep(3)
out, _ = run("ps aux | grep 'python.*main.py' | grep -v grep | head -1")
print(f"  Running: {'YES' if 'python' in out else 'NO'} {out[:60]}")

ssh.close()
print("\nDeploy complete!")
