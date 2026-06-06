import paramiko, json

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

# 登入 shareholder08
cmd1 = '''curl -s -X POST http://127.0.0.1:7862/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"shareholder08@aiforge.com","password":"SH267924"}' '''

stdin, stdout, stderr = client.exec_command(cmd1, timeout=10)
out = stdout.read().decode()
print("=== shareholder08 登录响应 ===")
print(out)

# 用返回的 token 拿用户信息
try:
    data = json.loads(out)
    token = data.get("access_token") or data.get("token") or ""
    if token:
        cmd2 = f'''curl -s http://127.0.0.1:7862/api/auth/me \
          -H "Authorization: Bearer {token}" '''
        stdin2, stdout2, stderr2 = client.exec_command(cmd2, timeout=10)
        out2 = stdout2.read().decode()
        print("\n=== token 查到的用户 ===")
        print(out2)
except:
    print("\n(token提取失败)")

# 也测试一下 xiaye 的正常登录对比
cmd3 = '''curl -s -X POST http://127.0.0.1:7862/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' '''
stdin3, stdout3, stderr3 = client.exec_command(cmd3, timeout=10)
out3 = stdout3.read().decode()
print("\n=== xiaye 正常登录响应 ===")
print(out3)

# 看看 auth.py 的登录逻辑
print("\n=== 登录代码 ===")
cmd4 = '''grep -n "def login\|def register\|verify_password\|get_user_by_email\|email.*password\|SELECT.*users" /home/ubuntu/aiforge/backend/api/auth.py | head -20'''
stdin4, stdout4, stderr4 = client.exec_command(cmd4, timeout=10)
out4 = stdout4.read().decode()
err4 = stderr4.read().decode()
print(out4[:1500])
if err4: print(err4[:200])

client.close()