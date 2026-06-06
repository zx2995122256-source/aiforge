#!/bin/bash
pkill -f 'uvicorn admin' 2>/dev/null
sleep 1
cd /home/ubuntu/aiforge/backend
nohup python3 -m uvicorn admin:app --host 127.0.0.1 --port 7863 > /tmp/admin.log 2>&1 &
sleep 2
curl -s -o /dev/null -w '%{http_code}' 'http://127.0.0.1:7863/?key=aiforge2026'
