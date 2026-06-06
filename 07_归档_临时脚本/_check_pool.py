import paramiko, json

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

stdin, stdout, stderr = client.exec_command('curl -s http://127.0.0.1:7861/api/pool/status', timeout=15)
data = json.loads(stdout.read().decode())

total = data['total_accounts']
active = data['active_accounts']
points = data['total_points']
continuous = data['continuous_reg_running']

status_count = {}
for acc in data['accounts']:
    s = acc.get('status', 'unknown')
    status_count[s] = status_count.get(s, 0) + 1

low = sum(1 for a in data['accounts'] if a.get('points', 0) < 50)
mid = sum(1 for a in data['accounts'] if 50 <= a.get('points', 0) < 150)
high = sum(1 for a in data['accounts'] if a.get('points', 0) >= 150)

print('=== Oiioii 账号池状态 ===')
print(f'账号总数: {total}')
print(f'活跃账号: {active}')
print(f'总积分: {points}')
print(f'自动注册: {"运行中" if continuous else "已停止"}')
print()
print('状态分布:')
for s, c in sorted(status_count.items(), key=lambda x: -x[1]):
    print(f'  {s}: {c} 个')
print()
print('积分分布:')
print(f'  低积分 (<50):   {low} 个')
print(f'  中积分 (50-150): {mid} 个')
print(f'  高积分 (>=150):  {high} 个')

client.close()