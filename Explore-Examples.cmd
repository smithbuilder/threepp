@echo off
cd /d "%~dp0"
echo.
echo   THREEPP - upstream examples
echo.
echo   1. Lighting and materials showpiece
echo   2. Water and atmospheric sky
echo   3. Procedural tree workshop
echo   4. Procedural forest
echo   5. Our original playground
echo   6. Scene editor
echo.
choice /c 123456 /n /m "Choose an example: "
if errorlevel 6 (call Launch-Editor.cmd & exit /b)
if errorlevel 5 (call Launch-Playground.cmd & exit /b)
if errorlevel 4 (powershell -NoProfile -ExecutionPolicy Bypass -File Run-Evaluation.ps1 -Example forest_demo & exit /b)
if errorlevel 3 (powershell -NoProfile -ExecutionPolicy Bypass -File Run-Evaluation.ps1 -Example tree_demo & exit /b)
if errorlevel 2 (powershell -NoProfile -ExecutionPolicy Bypass -File Run-Evaluation.ps1 -Example water & exit /b)
powershell -NoProfile -ExecutionPolicy Bypass -File Run-Evaluation.ps1 -Example showpiece
