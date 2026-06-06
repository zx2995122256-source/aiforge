import paramiko, json

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check existing tasks that completed
stdin, stdout, stderr = client.exec_command(
    """curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])" """,
    timeout=10
)
token = stdout.read().decode().strip()

# Get latest 10 completed tasks
stdin, stdout, stderr = client.exec_command(
    f'curl -s http://127.0.0.1:7862/api/gen/tasks?limit=30 -H "Authorization: Bearer {token}"',
    timeout=10
)
tasks = json.loads(stdout.read().decode())
if isinstance(tasks, dict):
    tasks_list = tasks.get("tasks", tasks)
else:
    tasks_list = tasks
print(f"Total tasks: {len(tasks_list)}")

completed_imgs = []
completed_vids = []
for t in tasks_list:
    if t.get("status") == "completed":
        url = t.get("result_url") or t.get("video_url") or ""
        if t.get("type") == "video":
            completed_vids.append(url)
        else:
            completed_imgs.append(url)
        print(f"  [{t.get('type')}] id={t.get('id')} prompt={t.get('prompt','?')[:40]} url={url[:60]}")

print(f"\nCompleted images: {len(completed_imgs)}")
print(f"Completed videos: {len(completed_vids)}")

# Now generate NEW prompts if needed
if len(completed_imgs) < 3:
    print("\nNeed more images, generating...")

if len(completed_vids) < 1:
    print("\nNeed video, generating...")

client.close()