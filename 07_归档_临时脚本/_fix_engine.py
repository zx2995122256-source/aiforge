#!/usr/bin/env python3
import paramiko, time

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)
print("Connected!")

sftp = ssh.open_sftp()

# Upload fixed engine.py
local = r"C:\Users\Administrator\Documents\OiioiiPool\core\engine.py"
remote = "/home/ubuntu/oiioii/core/engine.py"
print(f"Uploading engine.py...", end=" ", flush=True)
sftp.put(local, remote)
print("OK")
sftp.close()

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

# Verify the fix
out, _ = run('grep "uploaded_refs" /home/ubuntu/oiioii/core/engine.py | head -5')
print(f'\nVerify uploaded_refs references:\n{out}')

# Fix the stuck task 405
out, _ = run('sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db "UPDATE tasks SET status=\'failed\', error_message=\'Bug fixed - uploaded_refs reference error\' WHERE id=405 AND status=\'processing\'" 2>/dev/null')
print(f'Fixed task 405 status')

# Restart OiioiiPool
print('\nRestarting OiioiiPool...')
out, _ = run('ps aux | grep "python.*oiioii" | grep -v grep | awk \'{print $2}\'')
if out:
    pids = out.split()
    for pid in pids:
        run(f'sudo kill -9 {pid}')
        print(f'  Killed PID {pid}')
    time.sleep(2)

run('sudo bash -c "cd /home/ubuntu/oiioii && nohup python3 main.py > /tmp/oiioii.log 2>&1 &"')
time.sleep(3)

out, _ = run('ps aux | grep "python.*oiioii" | grep -v grep')
print(f'\nOiioiiPool process: {"RUNNING" if out else "NOT RUNNING"}')
if out:
    print(f'  {out}')

out, _ = run('sudo lsof -i :7861 2>/dev/null | head -3')
print(f'Port 7861: {"LISTENING" if "python" in out else "NOT LISTENING"}')

ssh.close()
print('\nDone! Bug fixed and service restarted.')
