#!/usr/bin/env python3
import os, sys
os.environ["GRADIO_SSR_MODE"] = "False"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr

with gr.Blocks(title="Test") as demo:
    gr.Markdown("# Hello")

try:
    demo.launch(server_name="127.0.0.1", server_port=7865, ssr_mode=False, debug=True)
except Exception as e:
    print(f"\n[LAUNCH ERROR] {e}", file=sys.stderr, flush=True)