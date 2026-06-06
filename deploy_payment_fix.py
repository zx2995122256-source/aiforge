import paramiko
import os

key_path = r"C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器\keys\ssh_key.pem"
key = paramiko.RSAKey.from_private_key_file(key_path)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', pkey=key)

# Patch payment.py - disable test mode
patch = '''
import re

with open('/home/ubuntu/aiforge/backend/api/payment.py', 'r') as f:
    content = f.read()

old = """    if not PAY_URL:
        pay_order(oid, f"manual_{oid}")
        return {"order_id": oid, "status": "paid", "msg": "支付未配置，已自动到账（测试模式）"}"""

new = """    if not PAY_URL:
        raise HTTPException(503, "支付系统暂未开放，请联系客服充值")"""

if old in content:
    content = content.replace(old, new)
    with open('/home/ubuntu/aiforge/backend/api/payment.py', 'w') as f:
        f.write(content)
    print("PATCHED: payment.py test mode disabled")
else:
    print("ALREADY PATCHED or pattern not found")
    # Check current state
    if "支付系统暂未开放" in content:
        print("Already has the fix")
    elif "已自动到账" in content:
        print("WARNING: Still has test mode!")
'''

stdin, stdout, stderr = ssh.exec_command(f'python3 -c {repr(patch)}')
print(stdout.read().decode())
print(stderr.read().decode())

# Restart backend
print("\nRestarting backend...")
stdin, stdout, stderr = ssh.exec_command('cd /home/ubuntu/aiforge && sudo systemctl restart aiforge')
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
