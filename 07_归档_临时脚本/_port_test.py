import socket
for port in [22, 80, 443, 7861, 7862, 8080]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        result = s.connect_ex(('43.134.205.136', port))
        status = "OPEN" if result == 0 else f"CLOSED/FILTERED(code={result})"
        print(f"Port {port}: {status}")
    except Exception as e:
        print(f"Port {port}: ERROR {e}")
    finally:
        s.close()
