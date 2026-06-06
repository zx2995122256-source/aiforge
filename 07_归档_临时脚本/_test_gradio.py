#!/usr/bin/env python3
import gradio as gr
import threading, time, httpx, os, sys

os.environ["GRADIO_SSR_MODE"] = "False"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

with gr.Blocks(title="Test") as demo:
    gr.Markdown("# Hello")

def test_server():
    time.sleep(4)
    for ip in ["127.0.0.1", "localhost"]:
        for port in [7863, 7864, 7865]:
            try:
                url = f"http://{ip}:{port}/gradio_api/startup-events"
                r = httpx.get(url, timeout=5)
                print(f"{ip}:{port} => Status: {r.status_code}")
                if r.status_code != 200:
                    print(f"  Body: {r.text[:500]}")
            except Exception as e:
                print(f"{ip}:{port} => {type(e).__name__}: {e}")

    # Also check the root
    for ip in ["127.0.0.1", "localhost"]:
        for port in [7863, 7864, 7865]:
            try:
                url = f"http://{ip}:{port}/"
                r = httpx.get(url, timeout=5)
                print(f"{ip}:{port}/ => Status: {r.status_code}")
            except Exception as e:
                print(f"{ip}:{port}/ => {type(e).__name__}: {e}")

threading.Thread(target=test_server, daemon=True).start()
demo.launch(server_name="127.0.0.1", server_port=7863, ssr_mode=False, quiet=False)