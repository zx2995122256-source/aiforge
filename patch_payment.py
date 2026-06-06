with open('/home/ubuntu/aiforge/backend/api/payment.py', 'r') as f:
    content = f.read()

old = '''    if not PAY_URL:
        pay_order(oid, f"manual_{oid}")
        return {"order_id": oid, "status": "paid", "msg": "\u652f\u4ed8\u672a\u914d\u7f6e\uff0c\u5df2\u81ea\u52a8\u5230\u8d26\uff08\u6d4b\u8bd5\u6a21\u5f0f\uff09"}'''

new = '''    if not PAY_URL:
        raise HTTPException(503, "\u652f\u4ed8\u7cfb\u7edf\u6682\u672a\u5f00\u653e\uff0c\u8bf7\u8054\u7cfb\u5ba2\u670d\u5145\u503c")'''

if old in content:
    content = content.replace(old, new)
    with open('/home/ubuntu/aiforge/backend/api/payment.py', 'w') as f:
        f.write(content)
    print("PATCHED: payment.py test mode disabled")
elif new in content:
    print("Already patched")
else:
    print("Pattern not found, checking content...")
    if "PAY_URL" in content:
        for i, line in enumerate(content.split('\n')):
            if 'PAY_URL' in line:
                print(f"  Line {i+1}: {line}")
