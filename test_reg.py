import requests, json, random, string

MAIL_TM = "https://api.mail.tm"
SUPABASE = "https://spb.oiioii.ai"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0.Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
OIIOII_API = "https://api.oiioii.ai"

# Create temp email
r = requests.get(f"{MAIL_TM}/domains", timeout=10)
domains = r.json().get("hydra:member", [])
domain = domains[0]["domain"] if domains else "mail.tm"
rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
email = f"oiio_{rand}@{domain}"
pwd = f"Oi{rand}!Pass1"

print(f"Email: {email}")

# Create mail account
r = requests.post(f"{MAIL_TM}/accounts", json={"address": email, "password": pwd}, timeout=15)
print(f"Mail create: {r.status_code}")

# Try Supabase signup
r = requests.post(f"{SUPABASE}/auth/v1/signup", json={
    "email": email,
    "password": pwd,
    "data": {"language": "zh", "nickname": email.split("@")[0]}
}, headers={"apikey": ANON_KEY, "Content-Type": "application/json"}, timeout=15)
print(f"Supabase signup: {r.status_code}")
print(f"Response: {r.text[:500]}")

# Try oiioii direct signin
r = requests.post(f"{OIIOII_API}/auth/signin_with_password", json={
    "email": email, "password": pwd, "tencentCaptcha": None,
    "inviteCode": "", "language": "zh", "nickname": email.split("@")[0],
    "signupOnNotFound": True
}, headers={"Content-Type": "application/json"}, timeout=15)
print(f"\noiioii signin: {r.status_code}")
print(f"Response: {r.text[:500]}")
