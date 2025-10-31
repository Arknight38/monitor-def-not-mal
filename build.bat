@echo off
echo ========================================
echo PC Monitor Build Script - Python 3.13 Fix
echo ========================================
echo.

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

REM Detect Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Detected Python version: %PYTHON_VERSION%

REM Check if Python 3.13+
echo %PYTHON_VERSION% | findstr "3.13" >nul
if not errorlevel 1 (
    echo.
    echo ========================================
    echo PYTHON 3.13 DETECTED
    echo ========================================
    echo.
    echo Nuitka doesn't fully support MinGW with Python 3.13 yet.
    echo.
    echo Choose your build method:
    echo 1. Use MSVC compiler (if installed)
    echo 2. Use PyInstaller instead (recommended - no compiler needed)
    echo 3. Downgrade to Python 3.12 (advanced)
    echo 4. Exit and install Python 3.12
    echo.
    set /p PYTHON313_CHOICE="Enter choice (1-4) [default: 2]: "
    if "%PYTHON313_CHOICE%"=="" set PYTHON313_CHOICE=2
    
    if "%PYTHON313_CHOICE%"=="1" goto USE_MSVC
    if "%PYTHON313_CHOICE%"=="2" goto USE_PYINSTALLER
    if "%PYTHON313_CHOICE%"=="3" goto DOWNGRADE_INFO
    if "%PYTHON313_CHOICE%"=="4" exit /b 0
)

REM Check for C compiler
echo Checking for C compiler...
set COMPILER_FOUND=0
set USE_MSVC_FLAG=

REM Check for MSVC first (required for Python 3.13)
where cl.exe >nul 2>&1
if not errorlevel 1 (
    echo [OK] Microsoft Visual C++ compiler found
    set COMPILER_FOUND=1
    set USE_MSVC_FLAG=--msvc=latest
    goto :compiler_ok
)

REM Check for gcc
where gcc >nul 2>&1
if not errorlevel 1 (
    echo [OK] GCC/MinGW found
    set COMPILER_FOUND=1
    goto :compiler_ok
)

:compiler_not_found
echo.
echo [WARNING] No compiler found!
echo.
echo For Python 3.13, you need MSVC or you can use PyInstaller.
echo.
echo Choose option:
echo 1. Install Visual Studio Build Tools (recommended for Nuitka)
echo 2. Use PyInstaller instead (no compiler needed)
echo.
set /p COMPILER_CHOICE="Enter choice (1-2) [default: 2]: "
if "%COMPILER_CHOICE%"=="" set COMPILER_CHOICE=2

if "%COMPILER_CHOICE%"=="1" (
    echo.
    echo Download Visual Studio Build Tools from:
    echo https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
    echo.
    echo After installing, restart terminal and run this script again.
    pause
    exit /b 1
)

if "%COMPILER_CHOICE%"=="2" goto USE_PYINSTALLER

:compiler_ok
echo.

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

echo.
echo ========================================
echo Starting Build with Nuitka...
echo ========================================
echo Compiler: %USE_MSVC_FLAG%
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
    echo.
    echo [ERROR] Server build failed!
    echo.
    echo Trying PyInstaller as fallback...
    goto USE_PYINSTALLER
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
    echo.
    echo [ERROR] Client build failed!
    echo.
    echo Trying PyInstaller as fallback...
    goto USE_PYINSTALLER
)
echo [SUCCESS] Client built successfully!
echo.

:SKIP_CLIENT

REM Clean up
if exist *.dist rmdir /s /q *.dist
if exist *.build rmdir /s /q *.build
if exist *.onefile-build rmdir /s /q *.onefile-build

goto BUILD_COMPLETE

REM ========================================
REM PYINSTALLER FALLBACK
REM ========================================
:USE_PYINSTALLER
echo.
echo ========================================
echo Using PyInstaller (Fallback)
echo ========================================
echo.

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Get build choice if not set
if "%BUILD_CHOICE%"=="" (
    echo Select what to build:
    echo 1. Build Server only
    echo 2. Build Client only
    echo 3. Build Both
    set /p BUILD_CHOICE="Enter choice (1-3) [default: 3]: "
    if "%BUILD_CHOICE%"=="" set BUILD_CHOICE=3
)

if "%CONSOLE_CHOICE%"=="" (
    echo Select console mode:
    echo 1. No console
    echo 2. With console
    set /p CONSOLE_CHOICE="Enter choice (1-2) [default: 1]: "
    if "%CONSOLE_CHOICE%"=="" set CONSOLE_CHOICE=1
)

if "%CONSOLE_CHOICE%"=="1" (
    set PY_CONSOLE_FLAG=--noconsole
) else (
    set PY_CONSOLE_FLAG=--console
)

REM Clean
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

if "%BUILD_CHOICE%"=="1" goto PY_BUILD_SERVER
if "%BUILD_CHOICE%"=="3" goto PY_BUILD_SERVER
goto PY_SKIP_SERVER

:PY_BUILD_SERVER
echo Building Server with PyInstaller...
python -m PyInstaller ^
    --onefile ^
    %PY_CONSOLE_FLAG% ^
    --name PCMonitor ^
    --hidden-import flask ^
    --hidden-import flask_cors ^
    --hidden-import pynput ^
    --hidden-import PIL ^
    --hidden-import requests ^
    --hidden-import win32gui ^
    --hidden-import win32process ^
    --hidden-import psutil ^
    --collect-all flask ^
    --collect-all flask_cors ^
    server.py

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)
echo [SUCCESS] Server built with PyInstaller!

:PY_SKIP_SERVER

if "%BUILD_CHOICE%"=="2" goto PY_BUILD_CLIENT
if "%BUILD_CHOICE%"=="3" goto PY_BUILD_CLIENT
goto BUILD_COMPLETE

:PY_BUILD_CLIENT
echo Building Client with PyInstaller...
python -m PyInstaller ^
    --onefile ^
    %PY_CONSOLE_FLAG% ^
    --name PCMonitorClient ^
    --hidden-import tkinter ^
    --hidden-import PIL ^
    --hidden-import requests ^
    --hidden-import flask ^
    --hidden-import flask_cors ^
    --collect-all flask ^
    --collect-all flask_cors ^
    client.py

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)
echo [SUCCESS] Client built with PyInstaller!

goto BUILD_COMPLETE

REM ========================================
REM MSVC INFO
REM ========================================
:USE_MSVC
echo.
echo Building with MSVC for Python 3.13...
set USE_MSVC_FLAG=--msvc=latest
goto compiler_ok

REM ========================================
REM DOWNGRADE INFO
REM ========================================
:DOWNGRADE_INFO
echo.
echo ========================================
echo Python 3.12 Installation Guide
echo ========================================
echo.
echo To use Python 3.12:
echo.
echo 1. Download Python 3.12 from:
echo    https://www.python.org/downloads/release/python-3120/
echo.
echo 2. During installation:
echo    - Check "Add Python to PATH"
echo    - Select "Customize installation"
echo    - Install for all users (optional)
echo.
echo 3. After installation:
echo    py -3.12 -m venv venv312
echo    venv312\Scripts\activate
echo    pip install -r requirements.txt
echo    build.bat
echo.
pause
exit /b 0

REM ========================================
REM BUILD COMPLETE
REM ========================================
:BUILD_COMPLETE
echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
dir dist\*.exe
echo.
echo Press any key to open dist folder...
pause >nul
explorer dist