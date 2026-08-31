@echo off
cd /d "%~dp0.."
if not exist logs mkdir logs
"venv\Scripts\python.exe" -m src.pipeline >> logs\daily_run.log 2>&1
