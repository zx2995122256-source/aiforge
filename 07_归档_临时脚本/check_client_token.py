import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check actual client upload function - is it token/points issue?
script = r'''
import requests, json, time

# Login to the external Oiioii API via one of the accounts
# First check account tokens
import subprocess
r = subprocess.run(["journalctl", "-u", "oiioii", "--since", "30 min ago", "--no-pager"], capture_output=True, text=True, timeout=10)
for l in r.stdout.split("\n"):
    if "upload_video" in l.lower() or "error" in l.lower() or "token" in l.lower() or "ECONN" in l or "epipe" in l:
        print(l)
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_client_logs.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_client_logs.py', timeout=15)
print(stdout.read().decode()[:2000])

# Also check the client.py token refresh
stdin, stdout, stderr = client.exec_command(
    'grep -n "def ensure_token\|def upload_video\|API_BASE\|check_quota\|check_points\|check_balance" /home/ubuntu/oiioii/core/client.py 2>/dev/null || grep -n "def ensure_token\|def upload_video\|API_BASE\|check_quota" /home/ubuntu/oiioii/core/core/client.py 2>/dev/null',
    timeout=10
)
print("\n=== Key functions ===")
print(stdout.read().decode()[:500])

client.close()