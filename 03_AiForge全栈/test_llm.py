import requests

key = "sk-nwbv2S8L7xszwt7KjFKAIxoFA9v4ZJfC"

# Try to list models
r = requests.get("https://token.sensenova.cn/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=10)
print("Models:", r.status_code, r.text[:1000])

# Try different model names
for model in ["DeepSeek-V4-Flash", "deepseek-chat", "sensenova-6.7-flash-lite", "DeepSeek-V3", "deepseek-v3", "SenseNova-V6"]:
    r = requests.post("https://token.sensenova.cn/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
        timeout=15)
    print(f"{model}: {r.status_code} {r.text[:150]}")
