#!/usr/bin/env python3
"""Check various httpx clients to find the exact pattern that fails"""
import sys, subprocess, time

proc = subprocess.Popen(
    [sys.executable, "-u", "-c", """
import uvicorn
from fastapi import FastAPI
app = FastAPI()
@app.get("/ping")
def ping():
    return {"message": "pong"}
uvicorn.run(app, host="127.0.0.1", port=7874, log_level="info")
"""],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
time.sleep(4)

import httpx

# Test 1: default client (FAILS)
r = httpx.get("http://127.0.0.1:7874/ping", timeout=10)
print(f"[default client] Status: {r.status_code}")

# Test 2: explicit transport (WORKS)
transport = httpx.HTTPTransport(retries=0)
client = httpx.Client(transport=transport)
r = client.get("http://127.0.0.1:7874/ping", timeout=10)
print(f"[explicit transport] Status: {r.status_code}")

# Test 3: mount transport on default client
client = httpx.Client()
client._transport = httpx.HTTPTransport(retries=0)
r = client.get("http://127.0.0.1:7874/ping", timeout=10)
print(f"[patched transport] Status: {r.status_code}")

# Test 4: pool_limits change
client = httpx.Client(pool_limits=httpx.PoolLimits(max_connections=1, max_keepalive_connections=0))
r = client.get("http://127.0.0.1:7874/ping", timeout=10)
print(f"[no keepalive] Status: {r.status_code}")

proc.terminate()
proc.wait()