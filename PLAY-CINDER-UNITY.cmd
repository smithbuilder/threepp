@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\unity\Run-Cinder.ps1" -Action Play -Revision cinder-unity-r25 %*
pause
