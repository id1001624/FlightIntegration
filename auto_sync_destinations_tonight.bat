@echo off
setlocal enabledelayedexpansion

echo ========================================
echo 設置今晚凌晨1:30自動同步機場目的地緩存
echo ========================================
echo.

:: 計算當前時間到凌晨1:30的秒數
for /f "tokens=1-3 delims=:" %%a in ("%time%") do (
    set /a current_seconds=%%a*3600+%%b*60+%%c
)

set /a target_seconds=1*3600+30*60
set /a wait_seconds=86400+target_seconds-current_seconds
if !wait_seconds! gtr 86400 set /a wait_seconds=!wait_seconds!-86400

set /a wait_hours=!wait_seconds!/3600
set /a wait_minutes=(!wait_seconds! %% 3600)/60

echo 當前時間: %time%
echo 目標時間: 01:30:00
echo 等待時間: !wait_seconds! 秒（約 !wait_hours! 小時 !wait_minutes! 分鐘）
echo.

echo ⚠️  重要提醒：
echo    - 此操作將同步所有台灣機場的目的地緩存數據
echo    - 預計需要 5-10 分鐘完成（依網路狀況而定）
echo    - 請確保電腦保持開機狀態直到凌晨1:30
echo    - 您可以最小化此視窗，但請勿關閉
echo.

echo 🔄 任務詳情：
echo    - 腳本將調用 Amadeus API 獲取最新目的地數據
echo    - 更新本地 airport_destinations 緩存表
echo    - 清理過期或無效的路線數據
echo    - 更新航班統計信息
echo.

set /p CONFIRM=確定要設置今晚的自動同步任務嗎？(Y/N): 
if /i not "%CONFIRM%"=="Y" (
    echo 任務已取消
    pause
    exit /b 0
)

echo.
echo ✅ 任務已設置！請不要關閉此視窗
echo    程序將在凌晨1:30自動執行機場目的地緩存同步
echo.

:: 等待到指定時間
echo ⏰ 等待中... 您可以最小化此視窗
timeout /t !wait_seconds! /nobreak > nul

:: 執行同步腳本
echo.
echo ========================================
echo 🚀 開始執行機場目的地緩存同步
echo 執行時間: %date% %time%
echo ========================================

:: 設置腳本路徑
set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend

cd /d "%BACKEND_DIR%"

:: 檢查並啟動虛擬環境
if exist "venv\Scripts\activate.bat" (
    echo 啟動虛擬環境...
    call venv\Scripts\activate.bat
) else (
    echo 警告: 找不到虛擬環境，使用系統Python
)

:: 執行同步（使用靜默模式避免交互）
echo 正在執行同步腳本...
python app\scripts\sync_airport_destinations.py > sync_destinations_log.txt 2>&1
set SYNC_RESULT=!ERRORLEVEL!

echo.
if !SYNC_RESULT! equ 0 (
    echo ✅ 機場目的地緩存同步成功完成！
    echo 📄 詳細日誌已保存到: %BACKEND_DIR%\sync_destinations_log.txt
) else (
    echo ❌ 機場目的地緩存同步失敗，錯誤代碼: !SYNC_RESULT!
    echo 📄 錯誤詳情請查看: %BACKEND_DIR%\sync_destinations_log.txt
    echo.
    echo 可能的解決方案：
    echo  1. 檢查網路連接是否正常
    echo  2. 確認 Amadeus API 憑證是否有效
    echo  3. 查看日誌文件以獲取詳細錯誤信息
)

echo.
echo ========================================
echo 任務執行完畢 - %date% %time%
echo ========================================
echo.
echo 任務結果將在5秒後自動關閉視窗
echo 如需查看詳細結果，請檢查日誌文件

timeout /t 5 /nobreak > nul
endlocal
exit /b !SYNC_RESULT! 