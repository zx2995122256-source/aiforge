import paramiko

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

script = """import sqlite3, random, string, time
c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
for i in range(10):
    code = 'AF' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    c.execute('INSERT INTO redeem_codes (code, points, created_at) VALUES (?,?,?)',
              (code, 10000, int(time.time())))
    print(f'  #{i+1} {code} - 10000')
c.commit()
c.close()
"""

sftp = client.open_sftp()
with sftp.file('/tmp/gen_codes.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/gen_codes.py', timeout=10)
out = stdout.read().decode()
err = stderr.read().decode()
print("=== 新兑换码 ===")
print(out)
if err: print(f"ERR: {err[:200]}")

# 验证总数
stdin2, stdout2, stderr2 = client.exec_command('python3 -c "import sqlite3;c=sqlite3.connect(chr(47)+chr(104)+chr(111)+chr(109)+chr(101)+chr(47)+chr(117)+chr(98)+chr(117)+chr(110)+chr(116)+chr(117)+chr(47)+chr(97)+chr(105)+chr(102)+chr(111)+chr(114)+chr(103)+chr(101)+chr(47)+chr(98)+chr(97)+chr(99)+chr(107)+chr(101)+chr(110)+chr(100)+chr(47)+chr(100)+chr(97)+chr(116)+chr(97)+chr(47)+chr(97)+chr(105)+chr(102)+chr(111)+chr(114)+chr(103)+chr(101)+chr(46)+chr(100)+chr(98));r=c.execute(chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(67)+chr(79)+chr(85)+chr(78)+chr(84)+chr(40)+chr(42)+chr(41)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(114)+chr(101)+chr(100)+chr(101)+chr(101)+chr(109)+chr(95)+chr(99)+chr(111)+chr(100)+chr(101)+chr(115)).fetchone();print(f\"兑换码总数: {r[0]}\")"', timeout=10)
out2 = stdout2.read().decode()
print(out2)
client.close()