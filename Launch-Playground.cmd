@echo off
cd /d "%~dp0"
if not exist "build\windows-gl\bin\Release\threepp_showcase.exe" (
  echo Build first: powershell -ExecutionPolicy Bypass -File Build-Playground.ps1
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Evaluation.ps1" -Example threepp_showcase
if errorlevel 1 pause
