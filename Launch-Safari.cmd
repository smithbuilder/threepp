@echo off
cd /d "%~dp0"
if not exist "build\windows-gl\bin\Release\timber_rally.exe" (
  echo Build first: powershell -ExecutionPolicy Bypass -File Build-Playground.ps1
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Evaluation.ps1" -Example timber_rally -Seconds 60 -Vehicle safari
if errorlevel 1 pause
