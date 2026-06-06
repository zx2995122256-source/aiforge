import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

cmds = [
    "echo '=== Services ==='",
    "sudo systemctl is-active aiforge && sudo systemctl is-active oiioii",
    "echo '=== Website ==='",
    "curl -s http://127.0.0.1:7862/ | head -c 80",
    "echo ''",
    "echo '=== Models ==='",
    "curl -s http://127.0.0.1:7862/api/gen/models | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f'Video models: {len(d.get(\\\"video\\\",{}))}, Image models: {len(d.get(\\\"image\\\",{}))}')\"",
    "echo '=== Pool ==='",
    "curl -s http://127.0.0.1:7861/api/pool/status | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f'Accounts: {d[chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(115)]}, Points: {d[chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(112)+chr(111)+chr(105)+chr(110)+chr(116)+chr(115)]}')\"",
    "echo '=== Config ==='",
    "grep POOL_MIN_TOTAL /home/ubuntu/aiforge/backend/config.py",
    "grep 'base = 100\\|base = 75\\|res_scale' /home/ubuntu/aiforge/backend/api/generate.py",
    "echo '=== Login ==='",
    "curl -s -X POST http://127.0.0.1:7862/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"xiaye@aiforge.com\",\"password\":\"zx4579561\"}' | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f'Login OK: {d[chr(116)+chr(111)+chr(107)+chr(101)+chr(110)][:20]}... role={d[chr(117)+chr(115)+chr(101)+chr(114)][chr(114)+chr(111)+chr(108)+chr(101)]}')\"",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    res = stdout.read().decode().strip()
    if res: print(res)

client.close()