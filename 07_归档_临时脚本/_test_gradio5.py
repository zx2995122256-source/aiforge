#!/usr/bin/env python3
"""Test if the FastAPI app itself works outside of Gradio's launch"""
import os, sys, threading, time, httpx, json
os.environ["GRADIO_SSR_MODE"] = "False"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Build a custom app that wraps the Gradio app
with gr.Blocks(title="Test") as demo:
    gr.Markdown("# Hello")

# Create a simple test app
test_app = FastAPI()

@test_app.get("/ping")
def ping():
    return {"status": "ok"}

# Mount Gradio app under /gradio
test_app.mount("/gradio", demo.app)

server = uvicorn.Server(uvicorn.Config(test_app, host="127.0.0.1", port=7867, log_level="debug"))
t = threading.Thread(target=server.run, daemon=True)
t.start()
time.sleep(3)

for url in [
    "http://127.0.0.1:7867/ping",
    "http://127.0.0.1:7867/gradio/",
]:
    try:
        r = httpx.get(url, timeout=10)
        print(f"GET {url} => Status: {r.status_code}", flush=True)
        print(f"  Body: {r.text[:200]}", flush=True)
    except Exception as e:
        print(f"GET {url} => {type(e).__name__}: {e}", flush=True)

server.should_exit = True
time.sleep(1)