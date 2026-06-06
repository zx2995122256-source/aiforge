#!/usr/bin/env python3
import subprocess, sys, os

KEY = r"C:\Users\Administrator\Documents\ssh_key.pem"
SERVER = "root@122.51.205.94"

def ssh_cmd(cmd, timeout=30):
    result = subprocess.run(
        ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15", SERVER, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return result.returncode, result.stdout, result.stderr

def deploy_file(local_path, remote_path):
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()
    encoded = content.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("$", "\\$")
    cmd = f"cat > {remote_path} << 'DEPLOY_EOF'\n{content}\nDEPLOY_EOF"
    rc, out, err = ssh_cmd(cmd, timeout=30)
    return rc == 0

print("=== Deploying to server ===")

files = [
    (r"C:\Users\Administrator\Documents\OiioiiPool\config.py", "/opt/OiioiiPool/config.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\client.py", "/opt/OiioiiPool/core/client.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\engine.py", "/opt/OiioiiPool/core/engine.py"),
]

for local, remote in files:
    print(f"  {os.path.basename(local)}...", end=" ", flush=True)
    if deploy_file(local, remote):
        print("OK")
    else:
        print("FAILED")
        sys.exit(1)

print("\nVerifying...")
rc, out, err = ssh_cmd("grep 'timeout.*900' /opt/OiioiiPool/config.py | head -1")
print(f"  Gemini Omni timeout check: {out.strip()[:80]}")

rc, out, err = ssh_cmd("grep 'initial_delay' /opt/OiioiiPool/core/client.py | head -2")
print(f"  initial_delay in client.py: {out.strip()[:80]}")

rc, out, err = ssh_cmd("grep 'RECOVERED' /opt/OiioiiPool/core/engine.py | head -1")
print(f"  Recovery logic in engine.py: {out.strip()[:80]}")

print("\nRestarting service...")
rc, out, err = ssh_cmd("cd /opt/OiioiiPool && pkill -f 'python.*main.py' 2>/dev/null; sleep 2; nohup python3 main.py > /dev/null 2>&1 & echo 'Process started'")
print(f"  Restart: {out.strip()}")

import time
time.sleep(3)
rc, out, err = ssh_cmd("ps aux | grep 'python.*main.py' | grep -v grep | head -1")
print(f"  Process running: {'YES' if 'python' in out else 'NO'}")
if 'python' in out:
    print(f"  PID: {out.strip()[:60]}")

print("\nDeploy complete!")
