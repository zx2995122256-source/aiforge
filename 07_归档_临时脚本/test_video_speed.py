import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Video download headers (should show Accept-Ranges)
stdin, stdout, stderr = client.exec_command(
    'curl -s -D - -o /dev/null http://127.0.0.1:7862/api/gen/file/275 2>&1 | head -15', timeout=15
)
print("=== HEADERS ===")
print(stdout.read().decode()[:500])

# Speed test with partial range (simulates browser seeking)
stdin, stdout, stderr = client.exec_command(
    'curl -s -o /dev/null -w "Speed: %{speed_download} B/s, Size: %{size_download} bytes" -r 0-1023 http://127.0.0.1:7862/api/gen/file/275', timeout=15
)
print(f"\n=== RANGE 0-1023 ===")
print(stdout.read().decode()[:200])

# Full file test
stdin, stdout, stderr = client.exec_command(
    'time curl -s -o /dev/null -w "Speed: %{speed_download} B/s" http://127.0.0.1:7862/api/gen/file/275', timeout=15
)
print(f"\n=== FULL SPEED ===")
print(stdout.read().decode()[:200])

client.close()