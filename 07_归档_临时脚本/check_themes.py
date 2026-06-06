import paramiko, json

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check if results exist
stdin, stdout, stderr = client.exec_command('cat /tmp/theme_results.json 2>/dev/null', timeout=10)
data = stdout.read().decode()
if data.strip():
    results = json.loads(data)
    print("=== RESULTS FOUND ===")
    print(json.dumps(results, indent=2))
else:
    print("No results yet. Checking running process...")
    stdin, stdout, stderr = client.exec_command('ps aux | grep gen_themes | grep -v grep', timeout=5)
    print(stdout.read().decode()[:300])
    
    # Maybe it finished but output not captured. Let me check by looking at latest tasks
    stdin, stdout, stderr = client.exec_command(
        """curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])" """,
        timeout=10
    )
    token = stdout.read().decode().strip()
    
    stdin, stdout, stderr = client.exec_command(
        f'curl -s http://127.0.0.1:7862/api/gen/tasks?limit=30 -H "Authorization: Bearer {token}"',
        timeout=10
    )
    tasks = json.loads(stdout.read().decode())
    if isinstance(tasks, dict): tasks = tasks.get("tasks", tasks)
    
    print(f"\nLatest completed tasks:")
    for t in tasks:
        if t.get("status") == "completed" and "GPT-Image2" in t.get("model", ""):
            print(f"  id={t['id']} oiioii_id={t.get('oiioii_task_id','?')} prompt={t.get('prompt','?')[:30]}")

client.close()