#!/usr/bin/env python3
import os, sys
os.environ["GRADIO_SSR_MODE"] = "False"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio.blocks
import httpx

original_get = httpx.get

def debugging_get(url, *args, **kwargs):
    print(f"[DEBUG] httpx.get: {url}", flush=True)
    try:
        result = original_get(url, *args, **kwargs)
        print(f"[DEBUG] Status: {result.status_code}", flush=True)
        print(f"[DEBUG] Body: {result.text[:1000]}", flush=True)
        return result
    except Exception as e:
        print(f"[DEBUG] Exception: {e}", flush=True)
        raise

gradio.blocks.httpx.get = debugging_get

import gradio as gr

with gr.Blocks(title="Test") as demo:
    gr.Markdown("# Hello")

try:
    demo.launch(server_name="127.0.0.1", server_port=7863, ssr_mode=False, quiet=False)
except Exception as e:
    print(f"\n[LAUNCH ERROR] {e}", file=sys.stderr, flush=True)