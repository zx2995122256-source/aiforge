with open(r'C:\Users\Administrator\Desktop\画布\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the insertion point: after `data = _rewrite_payload_urls(data)` and before `def _extract_task_id_from_text`
old = "            data = _rewrite_payload_urls(data)\n\n\n            def _extract_task_id_from_text"
new = """            data = _rewrite_payload_urls(data)

            # Auto-upgrade: gpt-image-2 + 4K → gpt-image-2-vip
            _model = str(data.get("model", "") if isinstance(data, dict) else "").strip().lower()
            _size = str(data.get("imageSize", "") if isinstance(data, dict) else "").strip().upper()
            if _model == "gpt-image-2" and _size == "4K":
                data["model"] = "gpt-image-2-vip"
                print(f"[auto-vip] Upgraded gpt-image-2 + 4K to gpt-image-2-vip")

            def _extract_task_id_from_text"""

content = content.replace(old, new)

with open(r'C:\Users\Administrator\Desktop\画布\server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: auto-vip upgrade logic added!")
