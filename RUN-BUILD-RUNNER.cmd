@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\unity\Prepare-Cinder.ps1" %*
if errorlevel 1 goto done
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\unity\Run-Cinder.ps1" -Action Build %*
:done
pause
