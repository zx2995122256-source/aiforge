with open(r'C:\Users\Administrator\Desktop\画布\api\imageUploadApi.js', 'rb') as f:
    content = f.read()

old = b"['startsWith']('http://localhost')||_0x5dd154['startsWith']('http://127.0.0.1')||_0x5dd154['startsWith']('/'))"
new = b"['startsWith']('http://localhost')||_0x5dd154['startsWith']('http://127.0.0.1')||_0x5dd154['startsWith']('http://192.168.')||_0x5dd154['startsWith']('/'))"

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\Administrator\Desktop\画布\api\imageUploadApi.js', 'wb') as f:
        f.write(content)
    print("SUCCESS!")
else:
    print("Pattern not found")
    print(f"Looking for: {old}")
