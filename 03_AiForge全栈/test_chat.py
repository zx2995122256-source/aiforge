import requests, json

base = "http://localhost:7862"

# Test chat endpoint directly without auth to see the validation error
r = requests.post(f"{base}/api/project/1/chat", 
    json={"message": "hello", "history": []},
    timeout=10)
print("No auth:", r.status_code, r.text[:300])

# Test with bad body
r = requests.post(f"{base}/api/project/1/chat", 
    json={"message": "hello"},
    timeout=10)
print("No history:", r.status_code, r.text[:300])
