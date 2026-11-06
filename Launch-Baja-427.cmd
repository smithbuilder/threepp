@echo off
cd /d "%~dp0"
if not exist "build\windows-gl\bin\Release\baja427_preview.exe" (
  echo Build the Baja 427 test scene first. See BAJA-427.md.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Evaluation.ps1" -Example baja427_preview -Seconds 60
set "BAJA_LAUNCH_EXIT=%errorlevel%"
if not "%BAJA_LAUNCH_EXIT%"=="0" pause
exit /b %BAJA_LAUNCH_EXIT%
