@echo off
echo 開始執行航班資料清理...
cd /d %~dp0

rem 設定 Python 環境
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=utf-8

rem 設定參數 - 預設保留 90 天的資料，只清理測試資料，啟用備份
set RETENTION_DAYS=90
set DATA_TYPE=test
set BACKUP=--backup

echo 清理 %RETENTION_DAYS% 天前的%DATA_TYPE%資料...

rem 執行清理腳本
python backend/app/scripts/cleanup_old_data.py --retention-days %RETENTION_DAYS% --data-type %DATA_TYPE% %BACKUP%

rem 檢查執行結果
if %ERRORLEVEL% NEQ 0 (
    echo 清理腳本執行失敗，錯誤碼: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo 清理完成！詳細日誌請查看 logs/cleanup_old_data.log

rem 暫停以便查看輸出
pause 