import paramiko

KEY_PATH = r"C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem"
HOST = "122.51.205.94"
USER = "ubuntu"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, key_filename=KEY_PATH, timeout=15)

# Run test in background
stdin, stdout, _ = ssh.exec_command("nohup python3 /tmp/test_refs_full.py > /tmp/test_refs_output.log 2>&1 & echo PID=$!")
out = stdout.read().decode()
print(out)

# Wait a moment then check
import time
time.sleep(10)

# Check if running and initial output
stdin, stdout, _ = ssh.exec_command("cat /tmp/test_refs_output.log")
print("=== Initial output ===")
print(stdout.read().decode()[:500])

stdin, stdout, _ = ssh.exec_command("ps aux | grep test_refs | grep -v grep | wc -l")
count = stdout.read().decode().strip()
print(f"Running processes: {count}")

ssh.close()
print("\nTest running in background. Will check progress in 3-4 min.")