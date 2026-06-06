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

for m in msgs:
    mid = m["id"]
    subj = m.get("subject", "")
    print(f"📧 [{subj}]")

    req2 = urllib.request.Request(f"https://api.mail.tm/messages/{mid}", headers={"Authorization": f"Bearer {TOKEN}"})
    c = json.loads(urllib.request.urlopen(req2).read())
    
    html_text = ""
    html_field = c.get("html", [])
    if isinstance(html_field, list):
        for part in html_field:
            if isinstance(part, dict):
                html_text += part.get("value", "")
            elif isinstance(part, str):
                html_text += part
    elif isinstance(html_field, str):
        html_text = html_field
    
    if not html_text:
        text_field = c.get("text", "")
        if isinstance(text_field, str):
            html_text = text_field

    if html_text:
        all_links = re.findall(r"https?://[^\s\"'<>]+", html_text)
        
        # Priority: supabase verify > oiioii > awstrack with verify
        verify_link = None
        for l in all_links:
            if "supabase" in l.lower() and "verify" in l.lower():
                verify_link = l
                break
        
        if not verify_link:
            for l in all_links:
                if "verify" in l.lower() or "token=" in l.lower():
                    verify_link = l
                    break
        
        if not verify_link:
            for l in all_links:
                if "oiioii" in l.lower() and "home" in l.lower():
                    verify_link = l
                    break
        
        if verify_link:
            # Decode the trackable link if needed
            # awstrack.me links redirect to the actual URL
            # Extract the supabase URL from the trackable link
            if "awstrack" in verify_link.lower():
                # The actual URL is URL-encoded inside the awstrack link
                decoded = urllib.request.unquote(verify_link)
                # Find the actual supabase URL
                match = re.search(r'(https?://[^/]+\.supabase\.co[^\s,]+)', decoded)
                if match:
                    verify_link = match.group(1)
                    print(f"\n  解码后的链接: {verify_link}")
            
            print(f"\n{'='*60}")
            print(f"✅ 邮箱: {EMAIL}")
            print(f"✅ 密码: {PASSWORD}")
            print(f"✅ 验证链接:")
            print(f"{verify_link}")
            print(f"{'='*60}")
            print(f"\n复制上面链接到浏览器打开即可激活账号！")
        else:
            print(f"\n  所有链接:")
            for l in all_links:
                print(f"    {l}")