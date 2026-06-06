import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Test OiioiiPool upload_video_ref endpoint
stdin, stdout, stderr = client.exec_command(
    'python3 -c "import requests; r = requests.post(\"http://127.0.0.1:7861/api/upload_video_ref\", files={\"file\": (\"test.mp4\", b\"fake video content\", \"video/mp4\")}, timeout=10); print(f\"Status: {r.status_code}\"); print(f\"Response: {r.text[:200]}\")"',
    timeout=15
)
print("=== OiioiiPool upload_video_ref ===")
print(stdout.read().decode()[:500])
err = stderr.read().decode().strip()
if err: print(f"ERR: {err[:300]}")

# List endpoints
stdin, stdout, stderr = client.exec_command(
    'python3 -c "import requests; r = requests.get(\"http://127.0.0.1:7861/openapi.json\", timeout=10); paths = list(r.json().get(\"paths\", {}).keys()); [print(p) for p in paths if \"upload\" in p or \"ref\" in p]"',
    timeout=10
)
print("\n=== Endpoints ===")
print(stdout.read().decode()[:500])

# Test via AiForge
stdin, stdout, stderr = client.exec_command(
    'TOKEN=$(curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d \'{"email":"xiaye@aiforge.com","password":"zx4579561"}\' | python3 -c "import sys,json;print(json.load(sys.stdin)[\'token\'])"); curl -s -X POST http://127.0.0.1:7862/api/gen/upload_video_ref -H "Authorization: Bearer $TOKEN" -F "file=@/tmp/test_upload.txt;filename=test.mp4;type=video/mp4"',
    timeout=15
)
print("\n=== AiForge upload ===")
print(stdout.read().decode()[:500])

client.close()