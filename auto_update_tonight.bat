@echo off
setlocal enabledelayedexpansion

echo 設置今晚凌晨2:00自動更新航班資料...

:: 計算當前時間到凌晨2:00的秒數
for /f "tokens=1-3 delims=:" %%a in ("%time%") do (
    set /a current_seconds=%%a*3600+%%b*60+%%c
)

set /a target_seconds=2*3600+0*60
set /a wait_seconds=86400+target_seconds-current_seconds
if !wait_seconds! gtr 86400 set /a wait_seconds=!wait_seconds!-86400

echo 當前時間: %time%
echo 目標時間: 02:00:00
echo 等待時間: !wait_seconds! 秒（約 !wait_seconds!/3600 小時 !wait_seconds! %% 3600 / 60 分鐘）

echo 請不要關閉此窗口！程序將在凌晨2:00自動執行航班資料更新。
echo 您可以最小化此窗口，但不要關閉它。

:: 等待到指定時間
timeout /t !wait_seconds! /nobreak > nul

:: 執行更新腳本
echo 開始執行航班資料更新 - %date% %time%
cd /d C:\Users\Aliothouo\OneDrive\文件\學校\AlphaVision\FlightIntegration\backend
echo 命令: python sync_flight_data.py flights-only --date 2025-04-07

:: 使用START命令在新的進程中啟動Python腳本
start /B python sync_flight_data.py flights-only --date 2025-04-07 > nul

:: 等待10分鐘（給腳本足夠時間同步數據）
echo 等待10分鐘讓腳本執行...
timeout /t 600 /nobreak > nul

:: 結束所有Python進程（確保腳本不會無限運行）
echo 終止所有Python進程以確保腳本不會無限運行...
taskkill /f /im python.exe > nul 2>&1

echo 航班資料更新完成（或已超時）- %date% %time%
echo 任務已完成，五秒後將自動關閉此窗口。
timeout /t 5 /nobreak > nul
endlocal