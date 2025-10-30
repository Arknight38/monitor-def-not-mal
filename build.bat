@echo off
echo Building PC Monitor Server...
echo.

REM Install PyInstaller if not installed
pip install pyinstaller

REM Build the executable
pyinstaller --onefile ^
    --name "PCMonitor" ^
    --icon=NONE ^
    --hidden-import=flask ^
    --hidden-import=flask_cors ^
    --hidden-import=pynput ^
    --hidden-import=PIL ^
    --hidden-import=win32gui ^
    --collect-all flask ^
    --collect-all flask_cors ^
    server.py

echo.
echo Build complete! Executable is in dist/PCMonitor.exe
echo.
echo Next steps:
echo 1. Copy PCMonitor.exe to target laptop
echo 2. Run it once to generate config.json
echo 3. Edit config.json with your API key
echo 4. Run PCMonitor.exe again
echo.
pause