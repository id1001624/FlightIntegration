@echo off
setlocal enabledelayedexpansion

echo ========================================
echo 航班目的地緩存自動同步工具
echo ========================================
echo.

:: 檢查參數
set EXECUTION_MODE=%1
if "%EXECUTION_MODE%"=="" set EXECUTION_MODE=interactive

:: 設置腳本路徑
set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend
set PYTHON_SCRIPT=%BACKEND_DIR%\app\scripts\sync_airport_destinations.py

echo 執行模式: %EXECUTION_MODE%
echo 腳本目錄: %SCRIPT_DIR%
echo 後端目錄: %BACKEND_DIR%
echo Python 腳本: %PYTHON_SCRIPT%
echo.

:: 檢查文件是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo 錯誤: 找不到同步腳本 %PYTHON_SCRIPT%
    if "%EXECUTION_MODE%"=="interactive" pause
    exit /b 1
)

:: 切換到後端目錄
cd /d "%BACKEND_DIR%"
echo 當前工作目錄: %CD%
echo.

:: 檢查並啟動虛擬環境
if exist "venv\Scripts\activate.bat" (
    echo 啟動虛擬環境...
    call venv\Scripts\activate.bat
) else (
    echo 警告: 找不到虛擬環境，使用系統Python
)

:: 執行同步腳本
echo [%date% %time%] 開始執行機場目的地緩存同步...
echo 命令: python app\scripts\sync_airport_destinations.py

if "%EXECUTION_MODE%"=="silent" (
    :: 靜默模式 - 直接執行
    python app\scripts\sync_airport_destinations.py > nul 2>&1
    set SYNC_RESULT=!ERRORLEVEL!
) else (
    :: 互動模式 - 顯示輸出
    python app\scripts\sync_airport_destinations.py
    set SYNC_RESULT=!ERRORLEVEL!
)

echo.
if !SYNC_RESULT! equ 0 (
    echo [%date% %time%] ✅ 機場目的地緩存同步完成！
) else (
    echo [%date% %time%] ❌ 機場目的地緩存同步失敗，錯誤代碼: !SYNC_RESULT!
)

echo.
echo ========================================
echo 同步任務執行完畢
echo ========================================

:: 根據執行模式決定是否暫停
if "%EXECUTION_MODE%"=="interactive" (
    echo.
    echo 按任意鍵關閉視窗...
    pause > nul
) else (
    echo 靜默模式執行完成，5秒後自動關閉
    timeout /t 5 /nobreak > nul
)

endlocal
exit /b !SYNC_RESULT! 