@echo off
cd /d "%~dp0"
echo.
echo   CHOOSE A WORLD
echo   1. Vehicle Tuning Playground - trails, jumps, wind tunnel
echo   2. Cinder Forest - Safari driving
echo   3. Original engine showcase
echo.
choice /c 123 /n /m "Choose 1, 2 or 3: "
if errorlevel 255 exit /b 1
if errorlevel 3 goto showcase
if errorlevel 2 goto forest
call "%~dp0Launch-Suspension-Playground.cmd"
exit /b %errorlevel%
:forest
call "%~dp0Launch-Safari.cmd"
exit /b %errorlevel%
:showcase
if not exist "build\windows-gl\bin\Release\threepp_showcase.exe" (
  echo Build first: powershell -ExecutionPolicy Bypass -File Build-Playground.ps1
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Evaluation.ps1" -Example threepp_showcase
if errorlevel 1 pause
