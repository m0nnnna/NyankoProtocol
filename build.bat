@echo off
REM Nyanko Protocol - build to EXE
REM Uses tools\python312 (embeddable Python 3.12 + pip). No system Python needed.
REM First run: run setup_build_env.ps1 or build.bat will run it.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "PY=%SCRIPT_DIR%tools\python312\python.exe"
set "PIP=%SCRIPT_DIR%tools\python312\Scripts\pip.exe"

echo.
echo   Building Nyanko Protocol...
echo.

REM Ensure tools\python312 exists
if not exist "%PY%" goto do_setup
if not exist "%PIP%" goto do_setup
goto do_build

:do_setup
echo Setup: downloading Python 3.12 embed and installing pip...
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup_build_env.ps1"
if errorlevel 1 goto setup_failed
if not exist "%PY%" goto setup_missing_py
if not exist "%PIP%" goto setup_missing_pip
goto do_build
:setup_failed
echo [ERROR] Setup failed.
pause
exit /b 1
:setup_missing_py
echo [ERROR] tools\python312\python.exe missing after setup.
pause
exit /b 1
:setup_missing_pip
echo [ERROR] tools\python312\Scripts\pip.exe missing after setup.
pause
exit /b 1

:do_build
set "PYTHONPATH="
echo Using: %PY%
"%PY%" --version

if not exist nyanko_icon.ico goto create_icon
goto install_deps
:create_icon
echo Creating icon...
"%PY%" create_icon.py
:install_deps
echo Installing deps...
"%PIP%" install -q -r requirements.txt pyinstaller pywin32

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Building EXE...
"%PY%" -m PyInstaller --clean NyankoProtocol.spec

if not exist "dist\NyankoProtocol.exe" goto build_failed
echo.
echo   OK: dist\NyankoProtocol.exe
echo.
pause
exit /b 0
:build_failed
echo [ERROR] Build failed.
pause
exit /b 1
