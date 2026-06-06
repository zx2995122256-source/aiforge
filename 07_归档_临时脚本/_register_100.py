import paramiko
import time
import json

KEY_PATH = r"C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem"
HOST = "122.51.205.94"
USER = "ubuntu"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, key_filename=KEY_PATH, timeout=15)

# Start batch registration of 100 accounts
print("=== Starting batch registration: 100 accounts ===")
stdin, stdout, _ = ssh.exec_command("curl -s -X POST 'http://localhost:7861/api/pool/register?count=100'")
resp = stdout.read().decode().strip()
print(f"Response: {resp}")

try:
    data = json.loads(resp)
    job_id = data.get("job_id", "")
    print(f"Job ID: {job_id}")
except:
    print("Failed to parse response")
    ssh.close()
    exit()

# Check current pool status
stdin, stdout, _ = ssh.exec_command("curl -s http://localhost:7861/api/stats")
stats = stdout.read().decode().strip()
current = json.loads(stats) if stats else {}
print(f"\nCurrent pool: {json.dumps(current, indent=2)}")

ssh.close()
print(f"\n=== Registration started in background ===")
print(f"Job ID: {job_id}")
print(f"Estimated time: ~50-100 minutes")
print("Will check progress periodically.")
print("You can check status anytime: curl http://122.51.205.94:7861/api/pool/register/{job_id}")