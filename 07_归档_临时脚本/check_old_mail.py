import json, urllib.request, re

with open("mailtm_creds.json") as f:
    creds = json.load(f)

TOKEN = creds["token"]
req = urllib.request.Request("https://api.mail.tm/messages", headers={"Authorization": f"Bearer {TOKEN}"})
data = json.loads(urllib.request.urlopen(req).read())
msgs = data.get("hydra:member", [])
print(f"Old mailbox: {creds['email']}")
print(f"Messages: {len(msgs)}")
for m in msgs:
    mid = m["id"]
    subj = m.get("subject", "")
    print(f"  [{subj}]")
    req2 = urllib.request.Request(f"https://api.mail.tm/messages/{mid}", headers={"Authorization": f"Bearer {TOKEN}"})
    c = json.loads(urllib.request.urlopen(req2).read())
    html_text = "".join(p.get("value", "") for p in c.get("html", []))
    links = re.findall(r"https?://[^\s\"'<>]+", html_text)
    for l in links:
        keywords = ["verify", "confirm", "验证", "activate", "signup", "oiioii"]
        if any(k in l.lower() for k in keywords):
            print(f"    >> {l}")