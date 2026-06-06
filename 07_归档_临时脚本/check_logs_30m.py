import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, time, subprocess, sys

# 1. Check OiioiiPool logs - what's happening with processing tasks
r = subprocess.run(["journalctl", "-u", "oiioii", "--since", "30 min ago", "--no-pager"], capture_output=True, text=True, timeout=10)
lines = r.stdout.split("\n")
print("=== Recent OiioiiPool events ===")
for l in lines[-50:]:
    if any(x in l for x in ["poll", "processing", "completed", "failed", "error", "Timeout", "Generated", "Task"]):
        print(f"  {l.strip()[:120]}")

# 2. Check AiForge logs
r2 = subprocess.run(["journalctl", "-u", "aiforge", "--since", "30 min ago", "--no-pager"], capture_output=True, text=True, timeout=10)
lines2 = r2.stdout.split("\n")
print("\n=== Recent AiForge events ===")
for l in lines2[-40:]:
    if any(x in l for x in ["poll", "processing", "completed", "failed", "error", "Timeout", "Task", "video", "image"]):
        print(f"  {l.strip()[:120]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_logs_30m.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_logs_30m.py', timeout=15)
print(stdout.read().decode()[:3000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()