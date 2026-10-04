@echo off
setlocal
cd /d "%~dp0\..\.."
py -3.12 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe packaging\build_native.py
if errorlevel 1 goto fail
start "" release
pause
exit /b 0
:fail
echo Build failed. Please check the output above.
pause
exit /b 1

