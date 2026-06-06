#!/usr/bin/env python3
"""Test uvicorn in main thread vs subprocess"""
import sys, subprocess, time, httpx

# Method 2: Run uvicorn as a subprocess
proc = subprocess.Popen(
    [sys.executable, "-c", """
import uvicorn
from fastapi import FastAPI
app = FastAPI()
@app.get("/ping")
def ping():
    return {"message": "pong"}
uvicorn.run(app, host="127.0.0.1", port=7869, log_level="info")
"""],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
time.sleep(4)

try:
    r = httpx.get("http://127.0.0.1:7869/ping", timeout=10)
    print(f"Method 2 (subprocess) => Status: {r.status_code}, Body: {r.text}", flush=True)
except Exception as e:
    print(f"Method 2 (subprocess) => {type(e).__name__}: {e}", flush=True)

proc.terminate()
time.sleep(1)

# Print what uvicorn output
out, _ = proc.communicate()
print(f"--- uvicorn output ---\n{out[-500:]}", flush=True)