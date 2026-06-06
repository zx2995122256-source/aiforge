#!/usr/bin/env python3
"""Test httpx 0.27.2"""
import sys, subprocess, time, httpx

proc = subprocess.Popen(
    [sys.executable, "-u", "-c", """
import uvicorn
from fastapi import FastAPI
app = FastAPI()
@app.get("/ping")
def ping():
    return {"message": "pong"}
uvicorn.run(app, host="127.0.0.1", port=7875, log_level="info")
"""],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
time.sleep(4)

print(f"httpx version: {httpx.__version__}")

# Default client test
r = httpx.get("http://127.0.0.1:7875/ping", timeout=10)
print(f"[default client] Status: {r.status_code}, Body: {r.text}")

proc.terminate()
proc.wait()