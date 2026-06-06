#!/usr/bin/env python3
"""Manual uvicorn test to isolate the 502 error"""
import os, sys, threading, time, httpx
os.environ["GRADIO_SSR_MODE"] = "False"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["GRADIO_SHARE"] = "False"

import gradio as gr
import uvicorn

with gr.Blocks(title="Test") as demo:
    gr.Markdown("# Hello")

# Build the app same way Gradio does
app = demo.app

# Start uvicorn manually in a thread
server = uvicorn.Server(uvicorn.Config(app=app, host="127.0.0.1", port=7866, log_level="debug"))
t = threading.Thread(target=server.run, daemon=True)
t.start()

time.sleep(3)

# Now manually test the startup-events endpoint
print("Testing startup-events...", flush=True)
for url in [
    "http://127.0.0.1:7866/gradio_api/startup-events",
    "http://localhost:7866/gradio_api/startup-events",
]:
    try:
        r = httpx.get(url, timeout=10)
        print(f"GET {url}", flush=True)
        print(f"  Status: {r.status_code}", flush=True)
        print(f"  Headers: {dict(r.headers)}", flush=True)
        print(f"  Body: '{r.text[:500]}'", flush=True)
    except Exception as e:
        print(f"GET {url} => {type(e).__name__}: {e}", flush=True)

# Also test a simple GET /
for url in ["http://127.0.0.1:7866/", "http://localhost:7866/"]:
    try:
        r = httpx.get(url, timeout=10)
        print(f"GET {url} => Status: {r.status_code}", flush=True)
    except Exception as e:
        print(f"GET {url} => {type(e).__name__}: {e}", flush=True)

server.should_exit = True
time.sleep(1)