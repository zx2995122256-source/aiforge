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

# Search for the retryTask function in the compiled JS
out, _ = run('python3 -c "import re; js=open(\'/home/ubuntu/aiforge/dist/assets/Workspace-CQ9o0z3E.js\').read(); m=re.search(r\'function [A-Za-z_]*\(t\)\{[^}]*currentTab[^}]*refImages[^}]*\}\', js); print(m.group()[:800] if m else \'NOT FOUND\')"')
print('=== retryTask compiled ===')
print(out)

# Also search for "重新生成" context
out, _ = run('python3 -c "js=open(\'/home/ubuntu/aiforge/dist/assets/Workspace-CQ9o0z3E.js\').read(); idx=js.find(\'重新生成\'); print(js[max(0,idx-200):idx+200] if idx>=0 else \'NOT FOUND\')"')
print('\n=== 重新生成 context ===')
print(out)

ssh.close()
