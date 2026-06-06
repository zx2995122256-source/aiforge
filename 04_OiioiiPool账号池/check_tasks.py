import urllib.request, json, time

base = "http://localhost:7861"

# Check the 3 tasks we submitted earlier
for tid in [1569, 1570, 1571]:
    try:
        resp = urllib.request.urlopen(base + "/api/task/" + str(tid))
        data = json.loads(resp.read().decode())
        print(f"Task #{tid}: status={data.get('status')} model={data.get('model_name','')} err={data.get('error_message','')[:80]}")
    except Exception as e:
        print(f"Task #{tid}: error - {e}")
