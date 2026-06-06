import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check AiForge backend poll function
stdin, stdout, stderr = client.exec_command(
    'grep -n -A 30 "def _poll_oiioii\|def _poll_task\|polling\|oiioii_task_id" /home/ubuntu/aiforge/backend/api/generate.py | head -60',
    timeout=10
)
print("=== AiForge poll function ===")
print(stdout.read().decode()[:2000])

# Check if there's print/log statements
stdin, stdout, stderr = client.exec_command(
    'grep -n "print\|log\|print(" /home/ubuntu/aiforge/backend/api/generate.py | grep -i "poll\|task\|complete\|fail\|timeout\|status" | head -20',
    timeout=10
)
print("\n=== AiForge polling prints ===")
print(stdout.read().decode()[:1000])

client.close()