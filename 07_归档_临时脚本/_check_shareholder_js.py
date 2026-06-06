import paramiko

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

# 看shareholder在JS里是什么内容
cmd1 = "grep -o '.{0,30}shareholder.{0,30}' /home/ubuntu/aiforge/dist/assets/index-B8_z5JjX.js"
stdin, stdout, stderr = client.exec_command(cmd1, timeout=10)
out = stdout.read().decode()
print("=== JS中 shareholder 上下文 ===")
print(out[:500])

# 也查查全局login里有没有隐藏逻辑
cmd2 = "grep -o '.{0,40}login.*admin.{0,40}' /home/ubuntu/aiforge/dist/assets/index-B8_z5JjX.js | head -5"
stdin2, stdout2, stderr2 = client.exec_command(cmd2, timeout=10)
out2 = stdout2.read().decode()
print("\n=== login+admin 上下文 ===")
print(out2[:500])

# 检查后台有没有注册到 shareholders
cmd3 = "python3 -c \"import sqlite3;c=sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db');r=c.execute('SELECT COUNT(*) FROM users WHERE email LIKE \\\"%shareholder%\\\"').fetchone();print(f'shareholder类用户: {r[0]}个')\""
stdin3, stdout3, stderr3 = client.exec_command(cmd3, timeout=10)
out3 = stdout3.read().decode()
print("\n=== shareholder类用户 ===")
print(out3[:500])

client.close()