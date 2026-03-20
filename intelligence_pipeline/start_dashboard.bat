@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: 이미 서버가 실행 중인지 확인
netstat -ano | findstr ":8899 " | findstr "LISTENING" > nul
if %errorlevel% == 0 (
    echo Server already running.
    start "" "http://localhost:8899"
    exit /b
)

:: 서버 시작 (백그라운드, 최소화)
cd /d "%~dp0"
start /min "" python -c "import os; os.environ['PYTHONIOENCODING']='utf-8'; exec(open('server.py').read())"

:: 서버 뜰 때까지 대기 (최대 10초)
set /a count=0
:wait
timeout /t 1 /nobreak > nul
netstat -ano | findstr ":8899 " | findstr "LISTENING" > nul
if %errorlevel% == 0 goto open
set /a count+=1
if %count% lss 10 goto wait

:open
start "" "http://localhost:8899"
