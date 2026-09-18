@echo off
REM ============================================================
REM  SubTrack - Lanceur portable (Windows)
REM  Usage : double-cliquez sur run.bat  (ou : set PORT=9000 && run.bat)
REM  Les donnees sont stockees dans .\data\subscriptions.db
REM ============================================================
cd /d "%~dp0"
if "%PORT%"=="" set PORT=8090
if "%DATA_DIR%"=="" set DATA_DIR=.\data
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

where py >nul 2>&1
if %ERRORLEVEL%==0 (set PYTHON_BIN=py -3) else (set PYTHON_BIN=python)

if exist vendor (
  echo -> Dependances embarquees ^(dossier vendor^).
  set PYTHONPATH=%CD%\vendor
  %PYTHON_BIN% -m uvicorn app.main:app --host 0.0.0.0 --port %PORT%
) else (
  if not exist .venv (
    echo -> Premiere execution : creation de l'environnement virtuel...
    %PYTHON_BIN% -m venv .venv
    .venv\Scripts\python.exe -m pip install --quiet --upgrade pip
    .venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
  )
  .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port %PORT%
)
