@echo off
chcp 65001 >nul 2>&1
setlocal EnableExtensions

set "PX_DIR=%~dp0"
cd /d "%PX_DIR%"

echo ============================================
echo   PanelX downloader / launcher
echo ============================================

REM --- already present locally? jump straight to launch ---
if exist "panelx.py" goto run

REM --- otherwise we need git to fetch it ---
where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: git is not installed.
    echo        Install git, or place panelx.py next to this script.
    pause
    exit /b 1
)

REM --- clone (HTTP/1.1 to dodge reset on some networks) ---
echo Cloning PanelX from GitHub...
git -c http.version=HTTP/1.1 clone https://github.com/Developerprit/PanelX.git
if not exist "PanelX\panelx.py" (
    echo ERROR: clone failed, panelx.py not found.
    pause
    exit /b 1
)
cd /d "PanelX"

:run
if exist "run.bat" (
    echo Starting PanelX...
    call run.bat
) else (
    echo ERROR: run.bat is missing in this folder.
    pause
    exit /b 1
)
endlocal
