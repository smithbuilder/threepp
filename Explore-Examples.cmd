@echo off
cd /d "%~dp0"
echo.
echo   THREEPP - conservative demo collection
echo   960x600 / 30 FPS maximum / 60-second supervised sessions
echo.
echo   1. Timber Run - driving study
echo   2. Engine Playground - three original scenes
echo   3. Materials showpiece - upstream
echo   4. Procedural tree workshop - upstream
echo   5. Procedural forest - upstream, reduced density
echo   6. Cinder Forest Rally - new playable candidate
echo.
choice /c 123456 /n /m "Choose a demo: "
if errorlevel 6 (call Launch-Cinder-Forest.cmd & exit /b)
if errorlevel 5 (powershell -NoProfile -ExecutionPolicy Bypass -File Run-Evaluation.ps1 -Example forest_demo & goto done)
if errorlevel 4 (powershell -NoProfile -ExecutionPolicy Bypass -File Run-Evaluation.ps1 -Example tree_demo & goto done)
if errorlevel 3 (powershell -NoProfile -ExecutionPolicy Bypass -File Run-Evaluation.ps1 -Example showpiece & goto done)
if errorlevel 2 (call Launch-Playground.cmd & exit /b)
call Launch-Timber-Run.cmd
exit /b
:done
if errorlevel 1 pause
