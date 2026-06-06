import requests
r = requests.post('http://localhost:7861/api/generate_video',
    json={'prompt':'A woman walking in snow','model':'Gemini Omni','ratio':'16:9','resolution':'720p','duration':5},
    timeout=60)
print(r.status_code, r.text[:500])
