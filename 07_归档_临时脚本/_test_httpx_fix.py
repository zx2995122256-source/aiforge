#!/usr/bin/env python3
"""Find exactly what httpx setting fixes the 502 issue"""
import sys, subprocess, time, httpx

proc = subprocess.Popen(
    [sys.executable, "-u", "-c", """
import uvicorn
from fastapi import FastAPI
app = FastAPI()
@app.get("/ping")
def ping():
    return {"message": "pong"}
uvicorn.run(app, host="127.0.0.1", port=7878, log_level="info")
"""],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
time.sleep(4)

# Test 1: default
r = httpx.get("http://127.0.0.1:7878/ping", timeout=10)
print(f"[1 default] Status: {r.status_code}")

# Test 2: Client with default args
client = httpx.Client()
r = client.get("http://127.0.0.1:7878/ping", timeout=10)
print(f"[2 Client()] Status: {r.status_code}")

# Test 3: Client with http1=True, http2=False
client = httpx.Client(http1=True, http2=False)
r = client.get("http://127.0.0.1:7878/ping", timeout=10)
print(f"[3 http1 only] Status: {r.status_code}")

# Test 4: Client with limits (no keepalive)
client = httpx.Client(limits=httpx.Limits(max_keepalive_connections=0, max_connections=10))
r = client.get("http://127.0.0.1:7878/ping", timeout=10)
print(f"[4 no keepalive] Status: {r.status_code}")

# Test 5: just using transport
transport = httpx.HTTPTransport()
client = httpx.Client(transport=transport)
r = client.get("http://127.0.0.1:7878/ping", timeout=10)
print(f"[5 transport()] Status: {r.status_code}")

# Test 6: transport with retries=0
transport = httpx.HTTPTransport(retries=0)
client = httpx.Client(transport=transport)
r = client.get("http://127.0.0.1:7878/ping", timeout=10)
print(f"[6 transport(retries=0)] Status: {r.status_code}")

proc.terminate()
proc.wait()