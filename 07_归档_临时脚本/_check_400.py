import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

# Check which accounts were used for tasks 400 and 401
stdin, stdout, stderr = ssh.exec_command('''python3 -c "
import sqlite3
conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.execute('SELECT t.id, t.account_id, a.email, a.points_remaining, t.status FROM tasks t JOIN accounts a ON t.account_id=a.id WHERE t.id IN (400,401)')
for r in cur.fetchall():
    print(r)
"''')
print("Tasks 400/401:")
print(stdout.read().decode()[:500])

# Check the full service log for these tasks
stdin, stdout, stderr = ssh.exec_command('journalctl -u oiioii --no-pager --since "5 min ago" 2>/dev/null | grep "Task #400\\|Task #401" | head -10')
print("Service logs:")
print(stdout.read().decode()[:500])

ssh.close()
