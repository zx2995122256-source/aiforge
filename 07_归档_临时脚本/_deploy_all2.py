#!/usr/bin/env python3
import paramiko, os, time

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)
print("Connected!")

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

# Fix dist dir permissions first
print("Fixing dist dir permissions...")
run('sudo chown -R ubuntu:ubuntu /home/ubuntu/aiforge/dist')
run('sudo rm -rf /home/ubuntu/aiforge/dist/*')
run('sudo mkdir -p /home/ubuntu/aiforge/dist/assets')

sftp = ssh.open_sftp()

# Upload frontend dist
dist_dir = r"C:\Users\Administrator\Documents\AiForge\frontend\dist"
remote_dist = "/home/ubuntu/aiforge/dist"

print("Uploading frontend dist...")
count = 0
for root, dirs, files in os.walk(dist_dir):
    for f in files:
        local_path = os.path.join(root, f)
        rel_path = os.path.relpath(local_path, dist_dir)
        remote_path = f"{remote_dist}/{rel_path.replace(os.sep, '/')}"
        
        remote_dir = os.path.dirname(remote_path).replace(os.sep, '/')
        if remote_dir != remote_dist:
            run(f'mkdir -p {remote_dir}')
        
        sftp.put(local_path, remote_path)
        count += 1

print(f"Uploaded {count} files")

sftp.close()

# Fix permissions for nginx
run('sudo chown -R www-data:www-data /home/ubuntu/aiforge/dist 2>/dev/null || true')

# Restart AiForge backend
print("Restarting AiForge backend...")
run("sudo systemctl restart aiforge")
time.sleep(3)

out, _ = run("sudo systemctl status aiforge | head -5")
print(f"Service: {out}")

# Test
out, _ = run('curl -s -o /dev/null -w "%{http_code}" http://localhost:7862/')
print(f"Frontend: HTTP {out}")

out, _ = run('curl -s http://localhost:7862/api/pay/notify -X POST -H "Content-Type: application/json" -d \'{"amount":0.01,"key":"test"}\'')
print(f"Payment API: {out}")

ssh.close()
print("\nDone!")
