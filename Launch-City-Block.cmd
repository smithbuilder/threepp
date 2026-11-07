@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Evaluation.ps1" -Example suspension_playground -World city -Vehicle safari -View 1 -Seconds 300
if errorlevel 1 pause
