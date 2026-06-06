@echo off
title OiioiiPool
cd "C:\Users\Administrator\Documents\OiioiiPool"
python main.py
if %errorlevel% neq 0 (
  "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" main.py
)
pause
