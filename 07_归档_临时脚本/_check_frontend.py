#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', password='zx4579561.', timeout=15)

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

# Check the deployed frontend JS for retryTask
out, _ = run('grep -o "retryTask\|重新生成\|refImages\|reference_images\|refVideo\|reference_video" /home/ubuntu/aiforge/dist/assets/Workspace-*.js | head -20')
print('=== Frontend JS keywords ===')
print(out)

# Check the full Workspace JS for the retry function
out, _ = run('cat /home/ubuntu/aiforge/dist/assets/Workspace-*.js | grep -o "retryTask[^}]*}" | head -3')
print('\n=== retryTask in deployed JS ===')
print(out[:500])

# Also check if the "重新生成" text is there
out, _ = run('grep -c "重新生成" /home/ubuntu/aiforge/dist/assets/Workspace-*.js')
print(f'\n重新生成 count: {out}')

# Check if old "重试" text is gone
out, _ = run('grep -c "重试" /home/ubuntu/aiforge/dist/assets/Workspace-*.js')
print(f'重试 count: {out}')

ssh.close()
