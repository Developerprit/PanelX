@echo off
chcp 65001 >nul 2>&1
setlocal EnableExtensions

set "PX_DIR=%~dp0"
if "%PX_HOST%"=="" set "PX_HOST=0.0.0.0"
if "%PX_PORT%"=="" set "PX_PORT=5221"

REM ---------------------------------------------------------------------------
REM Locate a REAL Python interpreter.
REM NOTE: on Windows the bare "python" command is often an App-Execution-Alias
REM stub that silently fails (zero output, non-zero exit) when launched from a
REM .bat. So we prefer "py -3" (Python Launcher) and fall back to a known
REM install path, only using bare "python" as a last resort.
REM ---------------------------------------------------------------------------
set "PYCMD=python"
set "PYOPT="

where py >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=py"
    set "PYOPT=-3"
    goto :launch
)

if exist "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PYCMD=C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
    goto :launch
)

:launch
echo Starting PanelX on http://%PX_HOST%:%PX_PORT%/
"%PYCMD%" %PYOPT% "%PX_DIR%panelx.py" --host %PX_HOST% --port %PX_PORT%
endlocal
