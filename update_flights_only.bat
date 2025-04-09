@echo off
powershell -Command "Write-Host '開始更新航班資料（僅航班）...' -ForegroundColor Green"
cd backend
python sync_flight_data.py flights-only --date 2025-04-07
powershell -Command "Write-Host '航班資料更新完成。' -ForegroundColor Green"
pause