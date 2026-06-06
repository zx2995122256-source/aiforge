import paramiko
import time

KEY_PATH = r"C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem"
HOST = "122.51.205.94"
USER = "ubuntu"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, key_filename=KEY_PATH, timeout=15)

print("Waiting 3 min for test progress...")
time.sleep(180)

print("=== Test output so far ===")
stdin, stdout, _ = ssh.exec_command("cat /tmp/test_refs_output.log")
print(stdout.read().decode())

# Check if still running
stdin, stdout, _ = ssh.exec_command("pgrep -f 'test_refs_full' | wc -l")
running = stdout.read().decode().strip()
print(f"\nStill running: {'Yes' if int(running) > 0 else 'No'}")

ssh.close()
print("\n=== Check complete ===")