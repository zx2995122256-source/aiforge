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

files = [
    (r"C:\Users\Administrator\Documents\AiForge\backend\api\payment.py", "/home/ubuntu/aiforge/backend/api/payment.py"),
    (r"C:\Users\Administrator\Documents\AiForge\backend\admin.py", "/home/ubuntu/aiforge/backend/admin.py"),
]

for local, remote in files:
    print(f"Uploading {local.split(chr(92))[-1]} -> {remote}...", end=" ", flush=True)
    sftp.put(local, remote)
    print("OK")

sftp.close()

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        return out, err
    except:
        return "(timeout)", ""

# Verify uploads
out, _ = run('grep -c "free_sign_notify" /home/ubuntu/aiforge/backend/api/payment.py')
print(f"\nVerify payment.py has free_sign_notify: {out}")

out, _ = run('grep -c "confirm_order" /home/ubuntu/aiforge/backend/admin.py')
print(f"Verify admin.py has confirm_order: {out}")

# Update systemd service with env vars
print("\nUpdating systemd service...")
service_content = """[Unit]
Description=AiForge Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/aiforge/backend
Environment=AIFORGE_FRONTEND_DIR=/home/ubuntu/aiforge/dist
Environment=AIFORGE_NOTIFY_KEY=aiforge2025
Environment=AIFORGE_WECHAT_QR=
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 7862
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target"""

# Write service file
run(f"echo '{service_content}' | sudo tee /etc/systemd/system/aiforge.service > /dev/null")

# Reload and restart
print("Reloading systemd...")
out, err = run("sudo systemctl daemon-reload")
print(f"  {'OK' if not err else err[:100]}")

print("Restarting AiForge...")
out, err = run("sudo systemctl restart aiforge")
print(f"  {'OK' if not err else err[:100]}")

time.sleep(3)

# Check if running
out, _ = run("sudo systemctl status aiforge | head -10")
print(f"\nService status:\n{out}")

out, _ = run("sudo lsof -i :7862 2>/dev/null | head -3")
print(f"\nPort 7862: {'RUNNING' if 'python' in out else 'NOT RUNNING'}")

# Test the notify endpoint
print("\nTesting notify endpoint...")
out, _ = run('curl -s -X POST http://localhost:7862/api/pay/notify -H "Content-Type: application/json" -d \'{"amount":0.01,"key":"test"}\'')
print(f"  Response: {out}")

ssh.close()
print("\nDone!")
