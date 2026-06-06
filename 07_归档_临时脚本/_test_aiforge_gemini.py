import paramiko

KEY_PATH = r"C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem"
HOST = "122.51.205.94"
USER = "ubuntu"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, key_filename=KEY_PATH, timeout=15)

# Quick service check
stdin, stdout, _ = ssh.exec_command("sudo systemctl is-active oiioii")
print(f"oiioii: {stdout.read().decode().strip()}")

stdin, stdout, _ = ssh.exec_command("sudo systemctl is-active aiforge")
print(f"aiforge: {stdout.read().decode().strip()}")

# Check if fix is deployed
stdin, stdout, _ = ssh.exec_command('grep "manualRefresh" /home/ubuntu/oiioii/core/client.py | head -3')
fix = stdout.read().decode().strip()
print(f"\nFix in client.py: {fix[:80] if fix else 'NOT FOUND!'}")

stdin, stdout, _ = ssh.exec_command('grep "manual_refresh" /home/ubuntu/oiioii/core/engine.py | head -3')
fix2 = stdout.read().decode().strip()
print(f"Fix in engine.py: {fix2[:80] if fix2 else 'NOT FOUND!'}")

# Submit a Gemini task via the AiForge proxy (port 7862) - this is what the frontend uses!
print("\n=== Testing via AiForge API (port 7862) ===")
import requests
body = {"prompt": "test from aiforge api", "model": "Gemini Omni", "ratio": "16:9", "resolution": "720p", "duration": 5}
r = requests.post(f"http://{HOST}:7862/api/gen/video", json=body, timeout=30)
res = r.json()
print(f"HTTP {r.status_code}")
print(f"Response: {res}")

if r.status_code == 200:
    aiforge_id = res.get("task_id", 0)
    oiioii_id = res.get("oiioii_task_id", 0)
    print(f"\nAiForge task: #{aiforge_id}")
    print(f"OiioiiPool task: #{oiioii_id}")

    # Wait and poll via AiForge API
    import time
    print("\n=== Polling AiForge API for 3 minutes ===")
    for i in range(18):  # 18 * 10s = 180s = 3min
        time.sleep(10)
        r2 = requests.get(f"http://{HOST}:7862/api/gen/task/{aiforge_id}", timeout=10)
        t = r2.json()
        status = t.get("status", "?")
        elapsed = (i + 1) * 10
        if status == "completed":
            print(f"[{elapsed}s] COMPLETED! url={t.get('result_url','')}")
            break
        elif status == "failed":
            print(f"[{elapsed}s] FAILED")
            break
        elif status == "timeout":
            print(f"[{elapsed}s] TIMEOUT")
            break
        else:
            if i % 3 == 0:
                print(f"[{elapsed}s] status={status}")

ssh.close()
print("\n=== Done ===")