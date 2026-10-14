@echo off
rem Runs the transcript downloader. First run sets up Python packages by itself.
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set "HERE=%~dp0"
set "PY=%HERE%.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo First run: setting up, this takes a minute...
  py -3 -m venv "%HERE%.venv" 2>nul || python -m venv "%HERE%.venv"
  if not exist "%PY%" (
    echo Python is not installed. Install it with:  winget install Python.Python.3.12
    exit /b 1
  )
)

rem Keep yt-dlp and the transcript library up to date, YouTube changes often.
"%PY%" -m pip install -q --disable-pip-version-check -U -r "%HERE%requirements.txt"
"%PY%" "%HERE%yt_transcripts.py" %*
