#!/usr/bin/env python3
"""Compare httpx vs requests vs urllib"""
import sys, subprocess, time

proc = subprocess.Popen(
    [sys.executable, "-u", "-c", """
import uvicorn
from fastapi import FastAPI
app = FastAPI()
@app.get("/ping")
def ping():
    return {"message": "pong"}
uvicorn.run(app, host="127.0.0.1", port=7872, log_level="info")
"""],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
time.sleep(4)

# Test 1: httpx
try:
    import httpx
    r = httpx.get("http://127.0.0.1:7872/ping", timeout=10)
    print(f"[httpx] Status: {r.status_code}, Body: {r.text}")
except Exception as e:
    print(f"[httpx] ERROR: {e}")

# Test 2: httpx with verify=False
try:
    import httpx
    r = httpx.get("http://127.0.0.1:7872/ping", timeout=10, verify=False)
    print(f"[httpx verify=False] Status: {r.status_code}, Body: {r.text}")
except Exception as e:
    print(f"[httpx verify=False] ERROR: {e}")

# Test 3: httpx disabling proxy auto-detection
try:
    import httpx
    client = httpx.Client(proxy=None, verify=False)
    r = client.get("http://127.0.0.1:7872/ping", timeout=10)
    print(f"[httpx no-proxy] Status: {r.status_code}, Body: {r.text}")
except Exception as e:
    print(f"[httpx no-proxy] ERROR: {e}")

# Test 4: requests (if installed)
try:
    import requests
    r = requests.get("http://127.0.0.1:7872/ping", timeout=10)
    print(f"[requests] Status: {r.status_code}, Body: {r.text}")
except ImportError:
    print("[requests] not installed")
except Exception as e:
    print(f"[requests] ERROR: {e}")

# Test 5: urllib
try:
    from urllib.request import urlopen
    r = urlopen("http://127.0.0.1:7872/ping", timeout=10)
    print(f"[urllib] Status: {r.status}, Body: {r.read().decode()}")
except Exception as e:
    print(f"[urllib] ERROR: {e}")

proc.terminate()
proc.wait()