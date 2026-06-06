import requests, json, time
# Test image generation
r = requests.post('http://localhost:7861/api/generate_image',
    json={'prompt': 'A beautiful sunset over mountains, photorealistic', 'model': 'GPT-Image2', 'ratio': '16:9', 'resolution': '1K'},
    timeout=60)
print("Image submit:", r.status_code, json.dumps(r.json(), indent=2)[:500])

if r.json().get('task_id'):
    tid = r.json()['task_id']
    for _ in range(12):
        time.sleep(10)
        r2 = requests.get(f'http://localhost:7861/api/task/{tid}', timeout=30)
        d = r2.json()
        print(f"  Poll {tid}: status={d.get('status')}, error={d.get('error','')[:100]}")
        if d.get('status') in ('completed', 'failed'):
            break
