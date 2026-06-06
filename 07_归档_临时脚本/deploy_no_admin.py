import paramiko, tarfile, io

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Upload frontend
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "dist")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/noamdin.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()

# Upload admin CLI tool
admin_script = """#!/usr/bin/env python3
\"\"\"
AiForge 管理工具 — 直接在服务器上用
用法: python3 /home/ubuntu/admin_tool.py <命令> [参数]

命令:
  redeem <积分>         生成兑换码
  add_points <uid> <分>  给用户加积分
  users                 查看所有用户
  pool                  查看账号池状态
  help                  显示帮助
\"\"\"
import requests, json, sys, time

BASE = "http://127.0.0.1:7862"

def login():
    r = requests.post(f"{BASE}/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
    return r.json()["token"]

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "--help", "-h"):
        print(__doc__)
        return

    cmd = sys.argv[1]
    token = login()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    if cmd == "redeem":
        points = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        r = requests.post(f"{BASE}/api/user/admin/redeem", json={"points": points}, headers=headers, timeout=10)
        data = r.json()
        print(f"🎫 兑换码: {data.get('code', '?')}")
        print(f"💰 积分值: {data.get('points', '?')}")
        print("用户可在网站「充值」页面输入兑换码")

    elif cmd == "add_points":
        uid = int(sys.argv[2])
        points = int(sys.argv[3])
        r = requests.post(f"{BASE}/api/user/admin/add_points", json={"user_id": uid, "points": points}, headers=headers, timeout=10)
        print(r.json().get("msg", "OK"))

    elif cmd == "users":
        r = requests.get(f"{BASE}/api/user/admin/users?limit=50", headers=headers, timeout=10)
        users = r.json()
        print(f"{'ID':>4} {'邮箱':<28} {'昵称':<10} {'积分':>6} {'角色':<6}")
        print("-"*60)
        for u in users:
            print(f"{u['id']:>4} {u['email']:<28} {u.get('nickname','?')[:8]:<10} {u['points']:>6} {u['role']:<6}")

    elif cmd == "pool":
        r = requests.get(f"{BASE}/api/pool/status", headers=headers, timeout=10)
        d = r.json()
        print(f"📊 账号池状态")
        print(f"   活跃账号: {d.get('active_accounts', '?')}")
        print(f"   总积分: {d.get('total_points', '?')}")
        print(f"   总账号: {d.get('total_accounts', '?')}")

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
"""

sftp = client.open_sftp()
with sftp.file('/home/ubuntu/admin_tool.py', 'w') as f:
    f.write(admin_script)
with sftp.file('/home/ubuntu/admin_tool.py', 'a') as f:
    pass  # Already written
sftp.close()

# Deploy
cmds = [
    "rm -rf /home/ubuntu/aiforge/dist && mkdir -p /home/ubuntu/aiforge && tar -xzf /tmp/noamdin.tar.gz -C /home/ubuntu/aiforge",
    "chmod +x /home/ubuntu/admin_tool.py",
    "sudo systemctl restart aiforge && sleep 2",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    if out: print(f"  {out[:200]}")

# Verify
print("\n=== VERIFY ===")
vcmds = [
    ("Site", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7862/"),
    ("NoAdmin", '''curl -s http://127.0.0.1:7862/ | python3 -c "import sys;html=sys.stdin.read();print('admin' if 'admin' in html.lower() else 'OK-没有admin')"'''),
    ("Tool", "python3 /home/ubuntu/admin_tool.py pool"),
]

for label, cmd in vcmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    res = stdout.read().decode().strip()[:200]
    print(f"  [{label}] {res}")

client.close()
print("\n✅ DONE!")