#!/usr/bin/env python3
"""Test uvicorn standalone with a simple FastAPI app"""
import asyncio, threading, time, httpx
from fastapi import FastAPI

app = FastAPI()

@app.get("/ping")
def ping():
    return {"message": "pong"}

# Method 1: Run uvicorn directly in a thread
import uvicorn
config = uvicorn.Config(app=app, host="127.0.0.1", port=7868, log_level="debug")
server = uvicorn.Server(config)

def run_server():
    server.run()

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(3)

try:
    r = httpx.get("http://127.0.0.1:7868/ping", timeout=10)
    print(f"Method 1 (thread) => Status: {r.status_code}, Body: {r.text}", flush=True)
except Exception as e:
    print(f"Method 1 (thread) => {type(e).__name__}: {e}", flush=True)

server.should_exit = True
time.sleep(1)