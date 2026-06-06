@echo off
cd /d "C:\Users\Administrator\Documents\OiioiiPool"
echo OiioiiPool - Starting...
if exist OiioiiPool.exe (
    OiioiiPool.exe
) else (
    python main.py
)
pause