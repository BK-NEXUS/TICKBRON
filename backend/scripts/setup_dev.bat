@echo off
rem TICKBRON backend dev setup (Windows). Run from anywhere: backend\scripts\setup_dev.bat
rem Creates venv, installs requirements, creates .env from .env.example (never overwrites it),
rem then migrates. Edit DB_USER / DB_PASSWORD / SECRET_KEY in backend\.env before migrating.
setlocal
cd /d "%~dp0.."

if not exist venv\Scripts\python.exe (
    echo Creating venv...
    python -m venv venv || exit /b 1
)
venv\Scripts\python.exe -m pip install --upgrade pip || exit /b 1
venv\Scripts\python.exe -m pip install -r requirements.txt || exit /b 1

if not exist .env (
    copy .env.example .env >nul
    echo Created backend\.env from .env.example.
    echo Edit DB_USER, DB_PASSWORD and SECRET_KEY in backend\.env, create the database, then run this script again.
    exit /b 0
)

rem Database must exist. Example as the postgres superuser:
rem   psql -U postgres -c "CREATE USER tickbron_user WITH PASSWORD '...' CREATEDB;"
rem   psql -U postgres -c "CREATE DATABASE tickbron OWNER tickbron_user;"
venv\Scripts\python.exe manage.py migrate || exit /b 1
echo Done. Run tests with: venv\Scripts\python.exe -m pytest --create-db
endlocal
