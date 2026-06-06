#!/usr/bin/env python3
"""Diagnose httpx 502 issue specifically"""
import sys, subprocess, time

proc = subprocess.Popen(
    [sys.executable, "-u", "-c", """
import uvicorn
from fastapi import FastAPI
app = FastAPI()
@app.get("/ping")
def ping():
    return {"message": "pong"}
uvicorn.run(app, host="127.0.0.1", port=7873, log_level="info")
"""],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
time.sleep(4)

import httpx
import os

# Test: check what httpx is doing
print(f"httpx version: {httpx.__version__}")
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'not set')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'not set')}")

# Test with HTTP/1.1 explicitly
try:
    client = httpx.Client(http1=True, http2=False, proxy=None)
    r = client.get("http://127.0.0.1:7873/ping", timeout=10)
    print(f"[httpx http1, no proxy] Status: {r.status_code}, Body: {r.text}")
except Exception as e:
    print(f"[httpx http1, no proxy] ERROR: {e}")

# Test with explicit transport
try:
    import httpx
    transport = httpx.HTTPTransport(retries=0)
    client = httpx.Client(transport=transport)
    r = client.get("http://127.0.0.1:7873/ping", timeout=10)
    print(f"[httpx custom transport] Status: {r.status_code}, Body: {r.text}")
except Exception as e:
    print(f"[httpx custom transport] ERROR: {e}")

# Test what happens when we catch the actual response
try:
    client = httpx.Client()
    r = client.get("http://127.0.0.1:7873/ping", timeout=10)
    print(f"[httpx default] Status: {r.status_code}")
    print(f"[httpx default] Headers: {dict(r.headers)}")
    print(f"[httpx default] HTTP version: {r.http_version}")
    print(f"[httpx default] Reason: {r.reason_phrase}")
    print(f"[httpx default] Elapsed: {r.elapsed}")
except Exception as e:
    print(f"[httpx default] ERROR: {type(e).__name__}: {e}")

proc.terminate()
proc.wait()