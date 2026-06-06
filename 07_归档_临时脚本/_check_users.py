import paramiko

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

# 查更多数据库信息
cmd = """python3 << 'PYEOF'
import sqlite3

db = '/home/ubuntu/aiforge/backend/data/aiforge.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

# 查看所有表
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("=== 所有表 ===")
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t[0]}")
    cnt = cur.fetchone()[0]
    print(f"  {t[0]}: {cnt} 条记录")

# 用户表所有字段
print()
print("=== 用户表 schema ===")
cur.execute("PRAGMA table_info(users)")
for col in cur.fetchall():
    print(f"  {col}")

# 全部用户
print()
print("=== 所有用户 ===")
cur.execute("SELECT * FROM users ORDER BY id")
users = cur.fetchall()
print(f"共 {len(users)} 个用户:")
print(f"{'id':<4} {'email':<30} {'nickname':<12} {'role':<10} {'points':<8} {'credits':<8} {'created_at'}")
print("-"*95)
for u in users:
    print(f"{u[0]:<4} {str(u[1]):<30} {str(u[2] or ''):<12} {str(u[3]):<10} {str(u[4]):<8} {str(u[5]):<8} {str(u[6])[:19]}")

# redeem_codes 表
print()
print("=== 兑换码表 ===")
cur.execute("PRAGMA table_info(redeem_codes)")
for col in cur.fetchall():
    print(f"  {col}")
cur.execute("SELECT * FROM redeem_codes")
codes = cur.fetchall()
print(f"共 {len(codes)} 个兑换码:")
for c in codes:
    print(f"  {c}")

# users表已使用兑换码记录
print()
print("=== 用户已使用兑换码 ===")
cur.execute("SELECT id, email, redeem_code_used FROM users WHERE redeem_code_used IS NOT NULL")
for r in cur.fetchall():
    print(f"  user#{r[0]} {r[1]} -> code: {r[2]}")

conn.close()
PYEOF
"""

stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
out = stdout.read().decode()
err = stderr.read().decode()
print(out)
if err:
    print(f"ERR: {err[:500]}")
client.close()