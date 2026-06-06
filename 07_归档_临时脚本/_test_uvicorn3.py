#!/usr/bin/env python3
"""Test with requests, browsers, and check asyncio"""
import sys, subprocess, time, os

# Start uvicorn in subprocess
proc = subprocess.Popen(
    [sys.executable, "-u", "-c", """
import uvicorn
from fastapi import FastAPI
app = FastAPI()
@app.get("/ping")
def ping():
    return {"message": "pong"}
uvicorn.run(app, host="127.0.0.1", port=7871, log_level="debug")
"""],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
time.sleep(5)

# Try different HTTP clients
import socket

# 1. Raw socket - bypass HTTP libraries entirely
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(10)
try:
    s.connect(("127.0.0.1", 7871))
    s.sendall(b"GET /ping HTTP/1.1\r\nHost: 127.0.0.1:7871\r\nConnection: close\r\n\r\n")
    data = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk
    print(f"Raw socket response:")
    print(data.decode("utf-8", errors="replace")[:1000])
except Exception as e:
    print(f"Socket error: {e}")
finally:
    s.close()

proc.terminate()
time.sleep(1)
out, _ = proc.communicate()
print(f"\n--- uvicorn output (last 300 chars) ---\n{out[-300:]}")