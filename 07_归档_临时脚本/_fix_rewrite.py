with open(r'C:\Users\Administrator\Desktop\画布\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the URL rewrite to also handle LAN IPs like 192.168.x.x, 10.x.x.x
# Current code:
# if s.startswith("https://") or s.startswith("http://"):
#     return obj
# This means any http/https URL that isn't localhost just passes through

# We need to intercept LAN IPs and rewrite them to the public base URL
# Add before the `if s.startswith("https://")` check

old = """                    if s.startswith("http://127.0.0.1") or s.startswith("http://localhost"):
                        if s.startswith("http://127.0.0.1"):
                            path = s[len("http://127.0.0.1"):]
                        else:
                            path = s[len("http://localhost"):]
                        if path.startswith(":8777") or path.startswith(":8800"):
                            path = path[5:]
                        if path:
                            return _public_base + path
                        return obj
                    if s.startswith("https://") or s.startswith("http://"):
                        return obj"""

new = """                    if s.startswith("http://127.0.0.1") or s.startswith("http://localhost"):
                        if s.startswith("http://127.0.0.1"):
                            path = s[len("http://127.0.0.1"):]
                        else:
                            path = s[len("http://localhost"):]
                        if path.startswith(":8777") or path.startswith(":8800"):
                            path = path[5:]
                        if path:
                            return _public_base + path
                        return obj
                    # Rewrite LAN IPs (192.168.x.x, 10.x.x.x, 172.16-31.x.x) to public base URL
                    _lan_patterns = ("http://192.168.", "http://10.", "http://172.16.", "http://172.17.", "http://172.18.", "http://172.19.", "http://172.20.", "http://172.21.", "http://172.22.", "http://172.23.", "http://172.24.", "http://172.25.", "http://172.26.", "http://172.27.", "http://172.28.", "http://172.29.", "http://172.30.", "http://172.31.")
                    if s.startswith(_lan_patterns):
                        import urllib.parse
                        parsed = urllib.parse.urlparse(s)
                        path = parsed.path or ""
                        if parsed.query:
                            path += "?" + parsed.query
                        if path:
                            return _public_base + path
                        return _public_base
                    if s.startswith("https://") or s.startswith("http://"):
                        return obj"""

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\Administrator\Desktop\画布\server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: LAN IP rewrite added to server.py")
else:
    print("FAILED: Pattern not found")
    idx = content.find("http://127.0.0.1")
    if idx >= 0:
        print(f"Context: {content[idx:idx+300]}")
