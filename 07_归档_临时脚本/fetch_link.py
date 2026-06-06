import json, urllib.request, re

with open("mailtm_creds.json") as f:
    creds = json.load(f)

EMAIL = creds["email"]
PASSWORD = creds["password"]
TOKEN = creds["token"]

print(f"邮箱: {EMAIL}")
print(f"密码: {PASSWORD}\n")

req = urllib.request.Request("https://api.mail.tm/messages", headers={"Authorization": f"Bearer {TOKEN}"})
data = json.loads(urllib.request.urlopen(req).read())
msgs = data.get("hydra:member", [])

print(f"共 {len(msgs)} 封邮件\n")

for m in msgs:
    mid = m["id"]
    subj = m.get("subject", "")
    print(f"📧 [{subj}]")

    req2 = urllib.request.Request(f"https://api.mail.tm/messages/{mid}", headers={"Authorization": f"Bearer {TOKEN}"})
    c = json.loads(urllib.request.urlopen(req2).read())
    
    # Try different content structures
    html_text = ""
    
    # Check if html is a list of parts
    html_field = c.get("html", [])
    if isinstance(html_field, list):
        for part in html_field:
            if isinstance(part, dict):
                html_text += part.get("value", "")
            elif isinstance(part, str):
                html_text += part
    elif isinstance(html_field, str):
        html_text = html_field
    
    # Try text field
    if not html_text:
        text_field = c.get("text", "")
        if isinstance(text_field, list):
            for part in text_field:
                if isinstance(part, dict):
                    html_text += part.get("value", "")
                elif isinstance(part, str):
                    html_text += part
        elif isinstance(text_field, str):
            html_text = text_field
    
    if html_text:
        links = re.findall(r"https?://[^\s\"'<>]+", html_text)
        print(f"  发现 {len(links)} 个链接:")
        for l in links:
            print(f"    {l}")
        
        # Find verification link
        verify = None
        for l in links:
            kw = ["verify", "confirm", "验证", "activate", "email"]
            if any(k in l.lower() for k in kw):
                verify = l
                break
        
        if not verify and links:
            oiioii_links = [l for l in links if "oiioii" in l.lower()]
            verify = oiioii_links[0] if oiioii_links else links[0]
        
        if verify:
            print(f"\n{'='*60}")
            print(f"✅ 验证链接:")
            print(f"{verify}")
            print(f"{'='*60}")
            print(f"\n邮箱: {EMAIL}")
            print(f"密码: {PASSWORD}")
            print(f"\n复制上面的链接在浏览器中打开即可激活账号！")
    
    # Also show raw content for debugging
    print(f"\n  [原始content结构]")
    print(f"  html type: {type(c.get('html', 'N/A')).__name__}")
    print(f"  text type: {type(c.get('text', 'N/A')).__name__}")
    print()