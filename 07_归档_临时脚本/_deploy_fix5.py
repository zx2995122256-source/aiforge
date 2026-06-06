#!/usr/bin/env python3
import subprocess, sys, os

KEY = r"C:\Users\Administrator\Documents\ssh_key.pem"
SERVER = "root@122.51.205.94"
REMOTE = "/opt/OiioiiPool"

files = [
    (r"C:\Users\Administrator\Documents\OiioiiPool\config.py", f"{REMOTE}/config.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\client.py", f"{REMOTE}/core/client.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core\engine.py", f"{REMOTE}/core/engine.py"),
]

for local, remote in files:
    print(f"Deploying {os.path.basename(local)}...")
    result = subprocess.run(
        ["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", local, f"{SERVER}:{remote}"],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode == 0:
        print(f"  OK")
    else:
        print(f"  FAILED: {result.stderr[:200]}")
        sys.exit(1)

print("\nRestarting service...")
result = subprocess.run(
    ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
     SERVER, "cd /opt/OiioiiPool && pkill -f 'python.*main.py'; sleep 2; nohup python3 main.py > /dev/null 2>&1 & echo restarted"],
    capture_output=True, text=True, timeout=30
)
print(f"  stdout: {result.stdout[:200]}")
print(f"  stderr: {result.stderr[:200]}")
print("Done!")
