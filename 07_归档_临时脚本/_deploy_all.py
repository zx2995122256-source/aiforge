#!/usr/bin/env python3
import paramiko, os, time

SERVER = "122.51.205.94"
USER = "ubuntu"
PASSWORD = "zx4579561."

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)
print("Connected!")

sftp = ssh.open_sftp()

# Upload backend files
backend_files = [
    (r"C:\Users\Administrator\Documents\AiForge\backend\models\db.py", "/home/ubuntu/aiforge/backend/models/db.py"),
    (r"C:\Users\Administrator\Documents\AiForge\backend\api\generate.py", "/home/ubuntu/aiforge/backend/api/generate.py"),
]

for local, remote in backend_files:
    print(f"Uploading {os.path.basename(local)}...", end=" ", flush=True)
    sftp.put(local, remote)
    print("OK")

# Upload frontend dist
dist_dir = r"C:\Users\Administrator\Documents\AiForge\frontend\dist"
remote_dist = "/home/ubuntu/aiforge/dist"

# Clear old dist
def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

print("Clearing old dist...")
run(f'sudo rm -rf {remote_dist}/*')
run(f'sudo mkdir -p {remote_dist}/assets')

# Upload dist files
print("Uploading frontend dist...")
for root, dirs, files in os.walk(dist_dir):
    for f in files:
        local_path = os.path.join(root, f)
        rel_path = os.path.relpath(local_path, dist_dir)
        remote_path = f"{remote_dist}/{rel_path.replace(os.sep, '/')}"
        
        # Create directories if needed
        remote_dir = os.path.dirname(remote_path).replace(os.sep, '/')
        if remote_dir != remote_dist:
            run(f'sudo mkdir -p {remote_dir}')
        
        sftp.put(local_path, remote_path)
        print(f"  {rel_path}")

sftp.close()

# Fix permissions
print("Fixing permissions...")
run(f'sudo chown -R www-data:www-data {remote_dist} 2>/dev/null; sudo chmod -R 755 {remote_dist}')

# Restart AiForge backend
print("Restarting AiForge backend...")
out, err = run("sudo systemctl restart aiforge")
time.sleep(3)

out, _ = run("sudo systemctl status aiforge | head -5")
print(f"Service status: {out}")

# Test the API
out, _ = run('curl -s http://localhost:7862/api/pay/notify -X POST -H "Content-Type: application/json" -d \'{"amount":0.01,"key":"test"}\'')
print(f"\nPayment notify test: {out}")

# Test frontend
out, _ = run('curl -s -o /dev/null -w "%{http_code}" http://localhost:7862/')
print(f"Frontend test: HTTP {out}")

ssh.close()
print("\nDone! All deployed.")
