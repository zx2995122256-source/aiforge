import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check syntax error
stdin, stdout, stderr = client.exec_command('python3 -c "import py_compile; py_compile.compile(\"/home/ubuntu/oiioii/api/server.py\", doraise=True)" 2>&1', timeout=10)
print(stdout.read().decode()[:500])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

# Get the specific lines around the error
stdin, stdout, stderr = client.exec_command(
    "sed -n '118,122p' /home/ubuntu/oiioii/api/server.py",
    timeout=10
)
print("\nLines 118-122:")
print(stdout.read().decode()[:300])

client.close()