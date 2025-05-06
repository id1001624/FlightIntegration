@echo off
echo 開始執行航班資料清理...
echo 執行時間: %date% %time%
cd /d %~dp0

rem 設定 Python 環境
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=utf-8

rem 設定參數 - 預設保留 90 天的資料（用於航班趨勢分析和預測功能）
set RETENTION_DAYS=90
set DATA_TYPE=all
set BACKUP=--backup

echo 清理 %RETENTION_DAYS% 天前的%DATA_TYPE%資料...
echo 清理操作將備份被刪除的數據

rem 檢查日誌目錄
if not exist "logs" mkdir logs

rem 執行清理腳本
echo 執行清理腳本...
python backend/app/scripts/cleanup_old_data.py --retention-days %RETENTION_DAYS% --data-type %DATA_TYPE% %BACKUP%

rem 檢查執行結果
if %ERRORLEVEL% NEQ 0 (
    echo 清理腳本執行失敗，錯誤碼: %ERRORLEVEL% >> logs\cleanup_error.log
    echo 時間: %date% %time% >> logs\cleanup_error.log
    echo 清理腳本執行失敗，錯誤碼: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo 航班資料清理完成！詳細日誌請查看 logs/cleanup_old_data.log
echo 清理完成時間: %date% %time%

rem 輸出完成訊息到日誌檔
echo %date% %time% - 自動清理完成，保留最近 %RETENTION_DAYS% 天資料 >> logs\auto_cleanup_history.log

rem 如果是直接執行則暫停以便查看輸出，如果是排程任務則不需要
if "%1"=="" pause 