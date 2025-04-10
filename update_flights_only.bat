@echo off
cd /d "%~dp0backend"
echo Starting flight data update...

for /f "delims=" %%a in ('powershell -Command "Get-Date -Format 'yyyy-MM-dd'"') do set TODAY=%%a
python sync_flight_data.py flights-only --date %TODAY%

echo Flight data update completed.
pause