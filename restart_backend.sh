#!/bin/bash
# Restart main backend (FastAPI on 7862)
pkill -f 'uvicorn main:app' 2>/dev/null
sleep 1
cd /home/ubuntu/aiforge/backend
nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 7862 > /tmp/backend.log 2>&1 &
sleep 2
curl -s -o /dev/null -w '%{http_code}' 'http://127.0.0.1:7862/docs'
