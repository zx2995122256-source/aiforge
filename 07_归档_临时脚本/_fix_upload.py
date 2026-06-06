with open(r'C:\Users\Administrator\Desktop\画布\api\imageUploadApi.js', 'rb') as f:
    content = f.read()

# The issue: `_processSingle` checks for 'http://localhost' and 'http://127.0.0.1' but not LAN IPs
# We need to add check for any local IP (192.168.x.x)

# Pattern to find: startsWith('http://localhost')||startsWith('http://127.0.0.1')||startsWith('/')
# Need to add: startsWith('http://192.168.')
old_pattern = b"'startsWith'('http://localhost')||_0x5dd154['startsWith'('http://127.0.0.1')||_0x5dd154['startsWith'('/')"
new_pattern = b"'startsWith'('http://localhost')||_0x5dd154['startsWith'('http://127.0.0.1')||_0x5dd154['startsWith'('/')||_0x5dd154['startsWith'('http://192.168.')"

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    with open(r'C:\Users\Administrator\Desktop\画布\api\imageUploadApi.js', 'wb') as f:
        f.write(content)
    print("SUCCESS: Added LAN IP detection for image upload skip")
else:
    # Try to find the actual pattern
    idx = content.find(b"startsWith")
    ctx = content[idx:idx+200]
    print(f"Pattern not found. Context: {ctx}")
    
    # Try a wider search
    idx2 = content.find(b"localhost")
    ctx2 = content[max(0,idx2-30):idx2+100]
    print(f"\nLocalhost context: {ctx2}")
