@echo off
cd /d "%~dp0"
echo.
echo   LA CATRINA / HYDRAULIC SPORT COUPE
echo.
echo   1. Drive the city
echo   2. Watch the street show
echo   3. Suspension playground
echo.
choice /c 123 /n /m "Choose 1, 2 or 3: "
if errorlevel 255 exit /b 1
if errorlevel 3 goto playground
if errorlevel 2 goto show
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Evaluation.ps1" -Example suspension_playground -World city -Vehicle catrina -View 1 -Seconds 300
goto done
:show
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Evaluation.ps1" -Example suspension_playground -World city -Vehicle catrina -View 1 -Hydraulics demo -AutoDrive -Seconds 300
goto done
:playground
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Evaluation.ps1" -Example suspension_playground -Vehicle catrina -View 1 -Seconds 300
:done
if errorlevel 1 pause
