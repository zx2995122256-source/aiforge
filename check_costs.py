import requests, json
r = requests.get("http://localhost:7861/api/models", timeout=15)
d = r.json()
print("=== VIDEO MODELS ===")
for k, v in d.get("video", {}).items():
    print(f"  {k}: cost_base={v.get('cost_base')}, cost_duration_scale={v.get('cost_duration_scale')}, resolutions={v.get('resolutions')}")
print("\n=== IMAGE MODELS ===")
for k, v in d.get("image", {}).items():
    print(f"  {k}: cost_base={v.get('cost_base')}, resolutions={v.get('resolutions')}")
