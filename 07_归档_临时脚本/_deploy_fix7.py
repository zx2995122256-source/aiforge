#!/usr/bin/env python3
import subprocess, sys, os, base64

KEY = r"C:\Users\Administrator\Documents\ssh_key.pem"
SERVER = "root@122.51.205.94"

def ssh_cmd(cmd, timeout=30):
    result = subprocess.run(
        ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15", SERVER, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return result.returncode, result.stdout, result.stderr

def deploy_file_small(local_path, remote_path):
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()
    b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    chunk_size = 4000
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    print(f"  {os.path.basename(local_path)}: {len(content)} bytes -> {len(chunks)} chunks")
    rc, _, err = ssh_cmd(f"echo -n '' > /tmp/deploy_b64.tmp")
    if rc != 0:
        print(f"  Failed to init temp file: {err[:100]}")
        return False
    for i, chunk in enumerate(chunks):
        rc, _, err = ssh_cmd(f"echo -n '{chunk}' >> /tmp/deploy_b64.tmp", timeout=15)
        if rc != 0:
            print(f"  Chunk {i} failed: {err[:100]}")
            return False
    rc, out, err = ssh_cmd(f"base64 -d /tmp/deploy_b64.tmp > {remote_path} && echo OK", timeout=15)
    if "OK" in out:
        rc2, out2, _ = ssh_cmd(f"wc -l {remote_path}")
        print(f"  Deployed: {out2.strip()}")
        return True
    else:
        print(f"  Decode failed: {err[:100]}")
        return False

print("=== Deploying to server ===")
files = [
    (r"C:\Users\Administrator\Documents\OiioiiPool\config.py", "/opt/OiioiiPool/config.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\client.py", "/opt/OiioiiPool/core/client.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\engine.py", "/opt/OiioiiPool/core/engine.py"),
]

for local, remote in files:
    print(f"Deploying {os.path.basename(local)}...")
    if not deploy_file_small(local, remote):
        print("FAILED!")
        sys.exit(1)

print("\nVerifying...")
rc, out, _ = ssh_cmd("grep 'timeout.*900' /opt/OiioiiPool/config.py | head -1")
print(f"  Gemini Omni timeout: {out.strip()[:80]}")

rc, out, _ = ssh_cmd("grep 'initial_delay' /opt/OiioiiPool/core/client.py | head -2")
print(f"  initial_delay: {out.strip()[:80]}")

rc, out, _ = ssh_cmd("grep 'RECOVERED' /opt/OiioiiPool/core/engine.py | head -1")
print(f"  Recovery logic: {out.strip()[:80]}")

print("\nRestarting...")
rc, out, _ = ssh_cmd("cd /opt/OiioiiPool && pkill -f 'python.*main.py' 2>/dev/null; sleep 2; nohup python3 main.py > /dev/null 2>&1 & echo started")
print(f"  {out.strip()}")

import time
time.sleep(3)
rc, out, _ = ssh_cmd("ps aux | grep 'python.*main.py' | grep -v grep | head -1")
print(f"  Running: {'YES' if 'python' in out else 'NO'} {out.strip()[:60]}")

print("\nDone!")
