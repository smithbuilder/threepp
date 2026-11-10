@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /nologo /std:c++20 /EHsc /O2 /MD /DWIN32 /D_WINDOWS /DNDEBUG /Iassets\unity\city\source\include /Iinclude /Iassets\unity\city\source /Ishowcase /Isrc/external/nlohmann tools\cinder-city-export\export_city.cpp /Fobuild\cinder-city-export\export_city.obj /Febuild\cinder-city-export\export_city.exe /link build\windows-gl\src\Release\threepp.lib build\windows-gl\src\external\glfw\src\glfw.dir\Release\glfw.lib ws2_32.lib user32.lib gdi32.lib shell32.lib ole32.lib advapi32.lib opengl32.lib
