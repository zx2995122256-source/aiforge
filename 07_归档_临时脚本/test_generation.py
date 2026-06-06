import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# 1. Login as admin
stdin, stdout, stderr = client.exec_command(
    '''curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])"''',
    timeout=10
)
token = stdout.read().decode().strip()
print(f"Token: {token[:50]}...")

# 2. Test image generation first (cheaper)
stdin, stdout, stderr = client.exec_command(
    f'''curl -s -X POST http://127.0.0.1:7862/api/gen/image -H "Content-Type: application/json" -H "Authorization: Bearer {token}" -d '{{"prompt":"a cute cat","model":"Flux Dev","ratio":"1:1","resolution":"1K","reference_images":[]}}' 2>&1 | head -c 500''',
    timeout=30
)
out = stdout.read().decode()
print(f"Image gen: {out[:200]}")

# 3. Test video generation
stdin, stdout, stderr = client.exec_command(
    f'''curl -s -X POST http://127.0.0.1:7862/api/gen/video -H "Content-Type: application/json" -H "Authorization: Bearer {token}" -d '{{"prompt":"a cat walking","model":"Vidu Q2","ratio":"16:9","resolution":"720p","duration":5,"reference_images":[],"reference_video":""}}' 2>&1 | head -c 500''',
    timeout=30
)
out = stdout.read().decode()
print(f"Video gen: {out[:200]}")

# 4. Check pool offers model
stdin, stdout, stderr = client.exec_command('curl -s http://127.0.0.1:7861/api/models | python3 -c "import sys,json;d=json.load(sys.stdin);v=d.get(chr(118)+chr(105)+chr(100)+chr(101)+chr(111),{});print([k for k in v.keys()][:5])"')
print(f"Pool models: {stdout.read().decode()[:200]}")

client.close()
